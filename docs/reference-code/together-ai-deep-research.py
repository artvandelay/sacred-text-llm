import argparse
import asyncio
import hashlib
import json
import os
import pickle
import re
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, List

import yaml
from dotenv import load_dotenv
from filelock import FileLock
from libs.utils.data_types import DeepResearchResult, DeepResearchResults, ResearchPlan, SourceList, UserCommunication
from libs.utils.generation import generate_pdf, save_and_generate_html
from libs.utils.llms import asingle_shot_llm_call, generate_toc_image
from libs.utils.log import AgentLogger
from libs.utils.podcast import generate_podcast_audio, generate_podcast_script, get_base64_audio, save_podcast_to_disk
from libs.utils.tavily_search import atavily_search_results

logging = AgentLogger("together.open_deep_research")

TIME_LIMIT_MULTIPLIER = 5


class DeepResearcher:
    def __init__(
        self,
        budget: int = 6,
        remove_thinking_tags: bool = False,
        max_queries: int = -1,
        max_sources: int = -1,
        max_completion_tokens: int = 4096,
        user_timeout: float = 30.0,
        interactive: bool = False,
        planning_model: str = "together_ai/meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        summarization_model: str = "together_ai/meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        json_model: str = "together_ai/meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        answer_model: str = "together_ai/deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
        debug_file_path: str | None = None,
        cache_dir: str | None = None,
        use_cache: bool = False,
        observer: Callable | None = None,
    ):
        self.budget = budget
        self.current_spending = 0
        self.remove_thinking_tags = remove_thinking_tags
        self.max_queries = max_queries
        self.max_sources = max_sources
        self.max_completion_tokens = max_completion_tokens
        self.user_timeout = user_timeout
        self.interactive = interactive
        self.planning_model = planning_model
        self.summarization_model = summarization_model
        self.json_model = json_model
        self.answer_model = answer_model
        self.debug_file_path = debug_file_path
        self.communication = UserCommunication()
        self.use_cache = use_cache

        # this is a little hack to make the observer optional
        self.observer = observer if observer is not None else lambda *args, **kwargs: None

        if self.use_cache:
            self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".open_deep_research_cache"
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            # Create a locks directory for the file locks
            self.locks_dir = self.cache_dir / ".locks"
            self.locks_dir.mkdir(parents=True, exist_ok=True)

        with open(os.path.join(os.path.dirname(__file__), "prompts.yaml"), "r") as f:
            self.prompts = yaml.safe_load(f)

    def __call__(self, topic: str) -> str:
        """
        Makes the DeepResearcher instance callable.
        Runs research on the given topic and returns the answer.

        Args:
            topic: The research topic or question

        Returns:
            The research answer as a string
        """
        loop = asyncio.new_event_loop()
        try:
            answer = loop.run_until_complete(self.research_topic(topic))

            pending = asyncio.all_tasks(loop)
            if pending:
                loop.run_until_complete(asyncio.wait(pending, timeout=10))

            return answer
        finally:
            loop.close()

    async def research_topic(self, topic: str) -> str:
        """Main method to conduct research on a topic"""

        self.observer(0, "Starting research")

        # Step 0: Clarify the research topic
        if self.interactive:
            self.observer(0.05, "Clarifying research topic")
            clarified_topic = await self.clarify_topic(topic)
            self.observer(0.1, "Research topic clarified")
        else:
            clarified_topic = topic

        logging.info(f"Topic: {clarified_topic}")

        # Step 1: Generate initial queries
        self.observer(0.15, "Generating research queries")
        queries = await self.generate_research_queries(clarified_topic)
        queries = [clarified_topic] + queries[: self.max_queries - 1]
        all_queries = queries.copy()
        logging.info(f"Initial queries: {queries}")
        self.observer(0.2, "Research queries generated")

        if len(queries) == 0:
            logging.error("No initial queries generated")
            return "No initial queries generated"

        # Step 2: Perform initial search
        self.observer(0.25, "Performing initial search")
        results = await self.search_all_queries(queries)
        logging.info(f"Initial search complete, found {len(results.results)} results")
        self.observer(0.3, "Initial search complete")

        # Step 3: Conduct iterative research within budget
        total_iterations = self.budget - self.current_spending
        for iteration in range(self.current_spending, self.budget):
            current_iteration = iteration - self.current_spending + 1
            progress = 0.3 + (0.4 * (current_iteration / total_iterations))
            self.observer(progress, f"Conducting research iteration {current_iteration}/{total_iterations}")

            # Evaluate if more research is needed
            additional_queries = await self.evaluate_research_completeness(clarified_topic, results, all_queries)

            # Filter out empty strings and check if any queries remain
            additional_queries = [q for q in additional_queries if q]
            if not additional_queries:
                logging.info("No need for additional research")
                self.observer(progress + 0.05, "Research complete - no additional queries needed")
                break

            # for debugging purposes we limit the number of queries
            additional_queries = additional_queries[: self.max_queries]
            logging.info(f"Additional queries: {additional_queries}")

            # Expand research with new queries
            self.observer(progress + 0.02, f"Searching {len(additional_queries)} additional queries")
            new_results = await self.search_all_queries(additional_queries)
            logging.info(f"Follow-up search complete, found {len(new_results.results)} results")
            self.observer(progress + 0.05, f"Found {len(new_results.results)} additional results")

            results = results + new_results
            all_queries.extend(additional_queries)

        # Step 4: Generate final answer with feedback loop
        self.observer(0.7, "Filtering and processing results")
        logging.info(f"Generating final answer for topic: {clarified_topic}")
        results = results.dedup()
        logging.info(f"Deduplication complete, kept {len(results.results)} results")
        filtered_results, sources = await self.filter_results(clarified_topic, results)
        logging.info(f"LLM Filtering complete, kept {len(filtered_results.results)} results")
        self.observer(0.8, f"Results filtered: kept {len(filtered_results.results)} sources")

        if self.debug_file_path:
            with open(self.debug_file_path, "w") as f:
                f.write(f"{results}\n\n\n\n{filtered_results}")
                logging.info(f"Debug file (web search results and sources) saved to {self.debug_file_path}")

        # Generate final answer
        self.observer(0.9, "Generating final research report")
        while True:
            answer = await self.generate_research_answer(clarified_topic, filtered_results, self.remove_thinking_tags)

            if not self.interactive or self.current_spending >= self.budget:
                self.observer(0.95, "Research complete")
                return answer

            logging.info(f"Answer: {answer}")
            user_feedback = await self.communication.get_input_with_timeout(
                "\nAre you satisfied with this answer? (yes/no) If no, please provide feedback: ",
                self.user_timeout * TIME_LIMIT_MULTIPLIER,
            )

            if user_feedback.lower() == "yes" or not user_feedback or user_feedback == "":
                return answer

            # Regenerate answer with user feedback
            clarified_topic = f"{clarified_topic}\n\nReport:{answer}\n\nAdditional Feedback: {user_feedback}"
            logging.info(f"Regenerating answer with feedback: {user_feedback}")
            self.current_spending += 1

    async def clarify_topic(self, topic: str) -> str:
        """
        Engage in a multi-turn conversation to clarify the research topic.
        Returns the clarified topic after user confirmation or timeout.

        Args:
            topic: The research topic to clarify
            timeout: Number of seconds to wait for user input (default: 10)
        """

        CLARIFICATION_PROMPT = self.prompts["clarification_prompt"]

        clarification = await asingle_shot_llm_call(
            model=self.planning_model, system_prompt=CLARIFICATION_PROMPT, message=f"Research Topic: {topic}"
        )

        logging.info(f"\nTopic Clarification: {clarification}")

        while self.current_spending < self.budget:
            user_input = await self.communication.get_input_with_timeout(
                "\nPlease provide additional details or type 'continue' to proceed with the research: ", self.user_timeout
            )

            if user_input.lower() == "continue" or not user_input or user_input == "":
                return (
                    topic if not hasattr(self, "_clarification_context") else f"{topic}\n\nContext: {self._clarification_context}"
                )

            # Store the clarification context
            if not hasattr(self, "_clarification_context"):
                self._clarification_context = user_input
            else:
                self._clarification_context += f"\n{user_input}"

            # Get follow-up clarification if needed
            clarification = await asingle_shot_llm_call(
                model=self.planning_model,
                system_prompt=CLARIFICATION_PROMPT,
                message=f"Research Topic: {topic}\nPrevious Context: {self._clarification_context}",
            )

            logging.info(f"\nFollow-up Clarification: {clarification}")
            self.current_spending += 1

        # helps typing
        return topic

    async def generate_research_queries(self, topic: str) -> list[str]:
        PLANNING_PROMPT = self.prompts["planning_prompt"]

        plan = await asingle_shot_llm_call(
            model=self.planning_model, system_prompt=PLANNING_PROMPT, message=f"Research Topic: {topic}"
        )

        logging.info(f"\n\nGenerated deep research plan for topic: {topic}\n\nPlan: {plan}\n\n")

        SEARCH_PROMPT = self.prompts["plan_parsing_prompt"]

        response_json = await asingle_shot_llm_call(
            model=self.json_model,
            system_prompt=SEARCH_PROMPT,
            message=f"Plan to be parsed: {plan}",
            response_format={"type": "json_object", "schema": ResearchPlan.model_json_schema()},
        )

        plan = json.loads(response_json)

        return plan["queries"]

    def _get_cache_path(self, query: str) -> Path:
        """Generate a cache file path for a given query using its hash"""
        query_hash = hashlib.md5(query.encode()).hexdigest()
        return self.cache_dir / f"tavily_{query_hash}.pkl"

    def _get_lock_path(self, cache_path: Path) -> Path:
        """Generate a lock file path for a given cache file"""
        return self.locks_dir / f"{cache_path.name}.lock"

    @contextmanager
    def _cache_lock(self, query: str):
        """Context manager for thread-safe cache operations"""
        cache_path = self._get_cache_path(query)
        lock_path = self._get_lock_path(cache_path)
        lock = FileLock(str(lock_path))
        try:
            with lock:
                yield cache_path
        finally:
            # Clean up lock file if it's stale
            if lock_path.exists() and not lock.is_locked:
                try:
                    lock_path.unlink()
                except FileNotFoundError:
                    pass

    def _save_to_cache(self, query: str, results: DeepResearchResults):
        """Save search results to cache in a thread-safe manner"""
        if not self.use_cache:
            return

        with self._cache_lock(query) as cache_path:
            with open(cache_path, "wb") as f:
                pickle.dump(results, f)

    def _load_from_cache(self, query: str) -> DeepResearchResults | None:
        """Load search results from cache if they exist in a thread-safe manner"""
        if not self.use_cache:
            return None

        try:
            with self._cache_lock(query) as cache_path:
                if cache_path.exists():
                    with open(cache_path, "rb") as f:
                        return pickle.load(f)
        except Exception as e:
            logging.warning(f"Failed to load cache for query '{query}': {e}")
        return None

    async def search_all_queries(self, queries: List[str]) -> DeepResearchResults:
        """Execute searches for all queries in parallel, using thread-safe cache"""
        tasks = []
        cached_results = []
        results_list = []

        for query in queries:
            # Try to load from cache first if caching is enabled
            cached_result = self._load_from_cache(query)
            if cached_result is not None:
                logging.info(f"Using cached results for query: {query}")
                cached_results.append(cached_result)
            else:
                # If not in cache, create search task
                tasks.append(self._search_and_cache(query))

        results_list.extend(cached_results)

        # Execute remaining searches in parallel
        if tasks:
            res_list = await asyncio.gather(*tasks)
            results_list.extend(res_list)

        # Combine all results
        combined_results = DeepResearchResults(results=[])
        for results in results_list:
            combined_results = combined_results + results

        return combined_results

    async def _search_and_cache(self, query: str) -> DeepResearchResults:
        """Perform a search and cache the results"""
        results = await self._search_engine_call(query)
        self._save_to_cache(query, results)
        return results

    async def _search_engine_call(self, query: str) -> DeepResearchResults:
        """Perform a single search"""

        if len(query) > 400:
            # NOTE: we are truncating the query to 400 characters to avoid Tavily Search issues
            query = query[:400]
            logging.info(f"Truncated query to 400 characters: {query}")

        response = await atavily_search_results(query)

        logging.info("Tavily Search Called.")

        RAW_CONTENT_SUMMARIZER_PROMPT = self.prompts["raw_content_summarizer_prompt"]

        # Create tasks for summarization
        summarization_tasks = []
        result_info = []
        for result in response.results:
            if result.raw_content is None:
                continue
            task = self._summarize_content_async(result.raw_content, query, RAW_CONTENT_SUMMARIZER_PROMPT)
            summarization_tasks.append(task)
            result_info.append(result)

        # Use return_exceptions=True to prevent exceptions from propagating
        summarized_contents = await asyncio.gather(*summarization_tasks, return_exceptions=True)
        # Filter out exceptions
        summarized_contents = [result for result in summarized_contents if not isinstance(result, Exception)]

        formatted_results = []
        for result, summarized_content in zip(result_info, summarized_contents):
            formatted_results.append(
                DeepResearchResult(
                    title=result.title,
                    link=result.link,
                    content=result.content,
                    raw_content=result.raw_content,
                    filtered_raw_content=summarized_content,
                )
            )
        return DeepResearchResults(results=formatted_results)

    async def _summarize_content_async(self, raw_content: str, query: str, prompt: str) -> str:
        """Summarize content asynchronously using the LLM"""
        logging.info("Summarizing content asynchronously using the LLM")

        result = await asingle_shot_llm_call(
            model=self.summarization_model,
            system_prompt=prompt,
            message=f"<Raw Content>{raw_content}</Raw Content>\n\n<Research Topic>{query}</Research Topic>",
        )

        return result

    async def evaluate_research_completeness(self, topic: str, results: DeepResearchResults, queries: List[str]) -> list[str]:
        """
        Evaluate if the current search results are sufficient or if more research is needed.
        Returns an empty list if research is complete, or a list of additional queries if more research is needed.
        """

        # Format the search results for the LLM
        formatted_results = str(results)
        EVALUATION_PROMPT = self.prompts["evaluation_prompt"]

        evaluation = await asingle_shot_llm_call(
            model=self.planning_model,
            system_prompt=EVALUATION_PROMPT,
            message=(
                f"<Research Topic>{topic}</Research Topic>\n\n"
                f"<Search Queries Used>{queries}</Search Queries Used>\n\n"
                f"<Current Search Results>{formatted_results}</Current Search Results>"
            ),
        )

        logging.info(f"Evaluation: {evaluation}")

        EVALUATION_PARSING_PROMPT = self.prompts["evaluation_parsing_prompt"]

        response_json = await asingle_shot_llm_call(
            model=self.json_model,
            system_prompt=EVALUATION_PARSING_PROMPT,
            message=f"Evaluation to be parsed: {evaluation}",
            response_format={"type": "json_object", "schema": ResearchPlan.model_json_schema()},
        )

        evaluation = json.loads(response_json)
        return evaluation["queries"]

    async def filter_results(self, topic: str, results: DeepResearchResults) -> tuple[DeepResearchResults, SourceList]:
        """Filter the search results based on the research plan"""

        # Format the search results for the LLM, without the raw content
        formatted_results = str(results)

        FILTER_PROMPT = self.prompts["filter_prompt"]

        filter_response = await asingle_shot_llm_call(
            model=self.planning_model,
            system_prompt=FILTER_PROMPT,
            message=(
                f"<Research Topic>{topic}</Research Topic>\n\n"
                f"<Current Search Results>{formatted_results}</Current Search Results>"
            ),
            # NOTE: This is the max_token parameter for the LLM call on Together AI, may need to be changed for other providers
            max_completion_tokens=4096,
        )

        logging.info(f"Filter response: {filter_response}")

        FILTER_PARSING_PROMPT = self.prompts["filter_parsing_prompt"]

        response_json = await asingle_shot_llm_call(
            model=self.json_model,
            system_prompt=FILTER_PARSING_PROMPT,
            message=f"Filter response to be parsed: {filter_response}",
            response_format={"type": "json_object", "schema": SourceList.model_json_schema()},
        )

        sources = json.loads(response_json)["sources"]

        logging.info(f"Filtered sources: {sources}")

        if self.max_sources != -1:
            sources = sources[: self.max_sources]

        # Filter the results based on the source list
        filtered_results = [results.results[i - 1] for i in sources if i - 1 < len(results.results)]

        return DeepResearchResults(results=filtered_results), sources

    async def generate_research_answer(self, topic: str, results: DeepResearchResults, remove_thinking_tags: bool = False):
        """
        Generate a comprehensive answer to the research topic based on the search results.
        Returns a detailed response that synthesizes information from all search results.
        """

        formatted_results = str(results)
        ANSWER_PROMPT = self.prompts["answer_prompt"]

        answer = await asingle_shot_llm_call(
            model=self.answer_model,
            system_prompt=ANSWER_PROMPT,
            message=f"Research Topic: {topic}\n\nSearch Results:\n{formatted_results}",
            # NOTE: This is the max_token parameter for the LLM call on Together AI, may need to be changed for other providers
            max_completion_tokens=self.max_completion_tokens,
        )

        # this is just to avoid typing complaints
        if answer is None or not isinstance(answer, str):
            logging.error("No answer generated")
            return "No answer generated"

        if remove_thinking_tags:
            # Remove content within <think> tags
            answer = self._remove_thinking_tags(answer)

        # Remove markdown code block markers if they exist at the beginning
        if answer.lstrip().startswith("```"):
            # Find the first line break after the opening backticks
            first_linebreak = answer.find("\n", answer.find("```"))
            if first_linebreak != -1:
                # Remove everything up to and including the first line break
                answer = answer[first_linebreak + 1 :]

            # Remove closing code block if it exists
            if answer.rstrip().endswith("```"):
                answer = answer.rstrip()[:-3].rstrip()

        return answer.strip()

    def _remove_thinking_tags(self, answer: str) -> str:
        """Remove content within <think> tags"""
        while "<think>" in answer and "</think>" in answer:
            start = answer.find("<think>")
            end = answer.find("</think>") + len("</think>")
            answer = answer[:start] + answer[end:]
        return answer


def main():
    from libs.utils.agent_factory import create_agent

    # Set up argument parser
    parser = argparse.ArgumentParser(description="Deep Research Tool")
    parser.add_argument("--write-pdf", action="store_true", help="Generate a PDF report of the research")
    parser.add_argument("--write-html", action="store_true", help="Generate an HTML report of the research")
    parser.add_argument("--add-toc-image", action="store_true", help="Generate a table of contents image")
    parser.add_argument("--write-podcast", action="store_true", help="Generate and save a podcast of the research")
    parser.add_argument(
        "--config",
        type=str,
        default="configs/open_deep_researcher_config.yaml",
        help="Path to configuration file (required)",
    )

    parser.add_argument("--output_file", type=str, default="", help="Path to the output file")
    args = parser.parse_args()

    load_dotenv()

    if os.environ.get("TOGETHER_API_KEY") is None or os.environ.get("TAVILY_API_KEY") is None:
        raise ValueError("TOGETHER_API_KEY and TAVILY_API_KEY must be set")

    # Use the agent factory with the config file
    logging.info(f"Using configuration from file: {args.config}")

    # Get the researcher instance directly instead of the callable function
    researcher_instance = create_agent(args.config, return_instance=True)

    # Get the callable function
    def researcher(topic):
        return researcher_instance(topic)

    topic = input("Enter your research topic: ")

    answer = researcher(topic)

    toc_image_url = None
    base64_audio = None
    audio_bytes = None

    if args.add_toc_image:
        # Use the instance's prompts
        toc_image_url = generate_toc_image(
            researcher_instance.prompts["data_visualization_prompt"], "together_ai/deepseek-ai/DeepSeek-V3", topic
        )
        logging.info(f"Table of contents image generated: {toc_image_url}")

    sanitized_topic_name = re.sub(r'[\\/*?:"<>|]', "_", topic)

    if args.write_podcast:
        logging.info("Generating podcast")
        script = generate_podcast_script(
            system_prompt=researcher_instance.prompts["create_podcast_script_prompt"],
            input_text=answer,
            podcast_name=f"Research on {topic[:50]}" if len(topic) > 50 else f"Research on {topic}",
        )
        audio_bytes = generate_podcast_audio(script)
        podcast_filename = f"podcast_{sanitized_topic_name}.mp3" if args.output_file == "" else f"{args.output_file}.mp3"
        save_podcast_to_disk(audio_bytes, podcast_filename)

        base64_audio = get_base64_audio(audio_bytes)

    if args.write_pdf:
        filename = f"research_report_{sanitized_topic_name}.pdf" if args.output_file == "" else f"{args.output_file}.pdf"
        generate_pdf(answer, filename)

    if args.write_html:
        filename = f"research_report_{sanitized_topic_name}.html" if args.output_file == "" else f"{args.output_file}.html"
        save_and_generate_html(answer, filename, toc_image_url, base64_audio=base64_audio)

    print(answer)


if __name__ == "__main__":
    main()