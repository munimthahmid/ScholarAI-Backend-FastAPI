import os
import logging
from typing import Optional

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
try:
    # Available in langgraph >= 0.2
    from langgraph.checkpoint.sqlite import SqliteSaver
except Exception:  # pragma: no cover
    SqliteSaver = None  # type: ignore


logger = logging.getLogger(__name__)


def get_chat_model() -> Optional[ChatOpenAI]:
    """Return a configured ChatOpenAI model if API key is available, else None.

    Honors env vars:
      - OPENAI_API_KEY
      - OPENAI_MODEL (default: gpt-5-mini; fallback: gpt-4o-mini)
      - OPENAI_BASE (optional)
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    base_url = os.getenv("OPENAI_BASE")

    try:
        llm = ChatOpenAI(model=model, api_key=api_key, base_url=base_url, streaming=True)
        # Lazy: do not hit network here; return configured client
        return llm
    except Exception as e:
        logger.warning(f"Failed to init OpenAI model '{model}': {e}. Falling back to gpt-4o-mini")
        try:
            return ChatOpenAI(model="gpt-4o-mini", api_key=api_key, base_url=base_url, streaming=True)
        except Exception as e2:
            logger.error(f"OpenAI client initialization failed: {e2}")
            return None


def get_checkpointer():
    """Return a LangGraph checkpointer based on env.

    GRAPHS_CHECKPOINTER: memory (default) | sqlite
    GRAPHS_CHECKPOINT_DB: path to sqlite db (default: ./data/checkpoints.db)
    """
    mode = os.getenv("GRAPHS_CHECKPOINTER", "memory").lower()
    if mode == "sqlite" and SqliteSaver is not None:
        db_path = os.getenv("GRAPHS_CHECKPOINT_DB", os.path.join("data", "checkpoints.db"))
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        return SqliteSaver.from_conn_string(f"sqlite:///{db_path}")
    return MemorySaver()
