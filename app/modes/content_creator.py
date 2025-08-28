"""
Content Creator Mode - Generates social media hooks from sacred texts.

This mode searches the vector store for passages related to a topic and
crafts an engaging tweet that invites readers to explore other modes of the
application.  It then auto-rates the tweet and optionally revises it based on a
critique so that the final output is more compelling.
"""

from __future__ import annotations

from typing import Generator, Dict, Any, List, Optional
import json

import ollama

from app.modes.base import BaseMode
from app.core.vector_store import VectorStore, ChromaVectorStore
from app import config as agent_config


class ContentCreatorMode(BaseMode):
    """Mode for generating engaging tweets from sacred text passages."""

    def __init__(self, llm_provider, vector_store):
        super().__init__(llm_provider, vector_store)
        if hasattr(vector_store, "query"):
            self.store: VectorStore = ChromaVectorStore(vector_store)
        else:
            self.store = vector_store

    def run(
        self, query: str, chat_history: Optional[List[Dict]] = None
    ) -> Generator[Dict[str, Any], None, str]:
        """Create a tweet inspired by sacred texts.

        The generator yields structured updates describing its progress and
        returns the final tweet string.
        """

        results = []
        traditions = agent_config.CONTENT_CREATOR_TRADITIONS

        rating_prompt = (
            "You are a meticulous social media editor. Rate the tweet from 1-10 "
            "for engagement and suggest improvements. Respond in JSON with keys "
            "'rating', 'critique', and 'improved'."
        )

        for trad in traditions:
            # Step 1: Retrieve passages for each tradition
            yield {
                "type": "searching",
                "tradition": trad,
                "content": f"Searching {trad} for insights on: {query}",
            }
            try:
                q_embed = ollama.embeddings(
                    model=agent_config.EMBEDDING_MODEL,
                    prompt=f"{query} {trad}",
                )["embedding"]
                sr = self.store.query_embeddings([q_embed], k=3)[0]
                docs = sr.documents
                metas = sr.metadatas
            except Exception as e:  # pragma: no cover - defensive
                yield {
                    "type": "error",
                    "tradition": trad,
                    "content": f"Search error: {e}",
                }
                continue

            passages = []
            for doc, meta in zip(docs, metas):
                source = meta.get("source", "Unknown source")
                passages.append({"source": source, "text": doc})
            yield {"type": "passages", "tradition": trad, "content": passages}

            # Step 2: Draft tweet in authoritative voice
            yield {
                "type": "drafting",
                "tradition": trad,
                "content": "Crafting initial tweet...",
            }
            passages_text = "\n".join(
                f"{i+1}. {p['text']}" for i, p in enumerate(passages)
            )
            prompt = f"""In a sharp, authoritative voice rooted in the {trad} tradition, craft a tweet (<=280 characters) linking the topic
"{query}" to these passages:
{passages_text}

The tweet should:
- offer a provocative hook into our 'contemplative' and 'deep_research' modes
- avoid hashtags except #SacredTexts
"""
            try:
                tweet = self.llm.generate_response(
                    [
                        {
                            "role": "system",
                            "content": "You craft terse, authoritative tweets based on passages.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    agent_config.OPENROUTER_CHAT_MODEL
                    if agent_config.LLM_PROVIDER == "openrouter"
                    else agent_config.OLLAMA_CHAT_MODEL,
                ).strip()
            except Exception as e:  # pragma: no cover - defensive
                yield {
                    "type": "error",
                    "tradition": trad,
                    "content": f"Tweet generation error: {e}",
                }
                continue

            yield {
                "type": "tweet_draft",
                "tradition": trad,
                "content": tweet,
            }

            # Step 3: Auto-rate with iterative critique
            final_tweet = tweet
            for i in range(agent_config.CONTENT_CREATOR_MAX_PASSES):
                yield {
                    "type": "evaluating",
                    "tradition": trad,
                    "content": f"Evaluating tweet (round {i + 1})...",
                }
                try:
                    rating_response = self.llm.generate_response(
                        [
                            {"role": "system", "content": rating_prompt},
                            {"role": "user", "content": final_tweet},
                        ],
                        agent_config.OPENROUTER_CHAT_MODEL
                        if agent_config.LLM_PROVIDER == "openrouter"
                        else agent_config.OLLAMA_CHAT_MODEL,
                    )
                    data = json.loads(rating_response)
                except Exception as e:  # pragma: no cover - defensive
                    yield {
                        "type": "error",
                        "tradition": trad,
                        "content": f"Rating failed: {e}",
                    }
                    break

                score = int(data.get("rating", 0))
                critique = data.get("critique", "")
                improved = data.get("improved", "")
                yield {
                    "type": "rating",
                    "tradition": trad,
                    "score": score,
                    "critique": critique,
                    "round": i + 1,
                }

                if (
                    score >= agent_config.CONTENT_CREATOR_TARGET_SCORE
                    or not improved
                    or i == agent_config.CONTENT_CREATOR_MAX_PASSES - 1
                ):
                    if score < agent_config.CONTENT_CREATOR_TARGET_SCORE and improved:
                        final_tweet = improved
                        yield {
                            "type": "revised",
                            "tradition": trad,
                            "content": "Tweet revised based on critique.",
                            "round": i + 1,
                        }
                    break

                final_tweet = improved
                yield {
                    "type": "revised",
                    "tradition": trad,
                    "content": "Tweet revised based on critique.",
                    "round": i + 1,
                }

            results.append({"tradition": trad, "tweet": final_tweet})

        yield {
            "type": "complete",
            "content": "Tweets prepared",
            "results": results,
        }
        return "\n\n".join(
            f"{r['tradition']}: {r['tweet']}" for r in results
        )
