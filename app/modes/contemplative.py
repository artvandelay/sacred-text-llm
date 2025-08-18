"""
Contemplative Mode - A simple mode for spiritual reflection.

This mode returns a single passage and a thoughtful question for contemplation.
"""

from typing import Generator, Dict, Any, List, Optional
import ollama

from app.modes.base import BaseMode
from app.core.vector_store import VectorStore, ChromaVectorStore
from app.modes.config import CONTEMPLATIVE_CONFIG
from app.agent import config as agent_config


class ContemplativeMode(BaseMode):
    """A mode focused on contemplative reflection rather than comprehensive research."""
    
    def __init__(self, llm_provider, vector_store):
        super().__init__(llm_provider, vector_store)
        self.config = CONTEMPLATIVE_CONFIG
        if hasattr(vector_store, "query"):
            self.store: VectorStore = ChromaVectorStore(vector_store)
        else:
            self.store = vector_store
        
    def run(self, query: str, chat_history: Optional[List[Dict]] = None) -> Generator[Dict[str, Any], None, str]:
        """
        Find a relevant passage and generate a contemplative question.
        
        This is a simple mode that demonstrates the architecture.
        """
        # Step 1: Search for relevant passage
        yield {"type": "searching", "content": f"Finding wisdom about: {query}"}
        
        try:
            # Get embedding for the query
            q_embed = ollama.embeddings(model=agent_config.EMBEDDING_MODEL, prompt=query)["embedding"]
            
            # Search the collection
            sr = self.store.query_embeddings([q_embed], k=self.config["max_results"])[0]
            docs = sr.documents
            metas = sr.metadatas
            
            if not docs:
                yield {"type": "error", "content": "No relevant passages found"}
                return "I couldn't find relevant passages for contemplation on this topic. Perhaps try rephrasing your question or exploring a different spiritual theme."
            
            # Get the top passage
            passage_text = docs[0]
            passage_meta = metas[0] if metas else {}
            source = passage_meta.get("source", "Unknown source")
            
            yield {
                "type": "passage_found",
                "source": source,
                "preview": passage_text[:150] + "..." if len(passage_text) > 150 else passage_text,
                "full_passage": passage_text
            }
            
        except Exception as e:
            yield {"type": "error", "content": f"Search error: {str(e)}"}
            return f"I encountered an error while searching for passages: {e}"
        
        # Step 2: Generate contemplative question
        yield {"type": "generating", "content": "Crafting a question for reflection..."}
        
        # Include chat history context if available
        chat_context = ""
        if chat_history:
            recent_history = chat_history[-2:]  # Last exchange
            for exchange in recent_history:
                role = exchange.get('role', '')
                content = exchange.get('content', '')
                if role == 'user':
                    chat_context += f"Recent question: {content}\n"
        
        # Prompt is self-contained in the mode (not in config)
        prompt = f"""You are a spiritual guide facilitating deep reflection.

Given this passage from sacred texts:
{passage_text}

Source: {source}

Generate a single, profound, open-ended question that:
1. Encourages deep personal reflection
2. Connects the passage to the reader's life
3. Opens new perspectives without providing answers

The question should be contemplative, not academic."""
        
        if chat_context:
            prompt = f"{chat_context}\n{prompt}\n\nConsider the conversational context when crafting your question."
        
        try:
            # Call LLM to generate question
            response = self.llm.generate_response(
                [
                    {
                        "role": "system",
                        "content": "You are a wise spiritual guide who helps people engage in deep contemplative practice. Your questions should invite personal reflection and inner exploration."
                    },
                    {"role": "user", "content": prompt}
                ],
                agent_config.OPENROUTER_CHAT_MODEL if agent_config.LLM_PROVIDER == "openrouter" else agent_config.OLLAMA_CHAT_MODEL
            )
            
            contemplative_question = response.strip()
            
        except Exception as e:
            yield {"type": "error", "content": f"Question generation error: {str(e)}"}
            # Fallback to a simple reflective question
            contemplative_question = f"How might the wisdom in this passage speak to your current life situation and spiritual journey?"
        
        # Format final response
        final_response = f"""**Sacred Text for Contemplation:**

*"{passage_text}"*

**Source:** {source}

---

**For Your Reflection:**

{contemplative_question}

---

*Take some time to sit quietly with this passage and question. Allow the wisdom to settle into your heart and see what insights arise naturally.*"""
        
        yield {
            "type": "complete", 
            "content": "Contemplative reflection prepared",
            "question_preview": contemplative_question[:100] + "..." if len(contemplative_question) > 100 else contemplative_question
        }
        
        return final_response
