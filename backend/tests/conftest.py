"""
Shared pytest fixtures for the HealthFirst Pharmacy Chatbot test suite.

Path setup is handled here so both test modules can import directly from
the `backend/` package root without any additional configuration.
"""

import os
import sys

# Add the backend root to sys.path so test modules can import main,
# conversation_manager, and llm_engine directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from starlette.testclient import TestClient

import main
from conversation_manager import ConversationManager


@pytest.fixture
def fresh_manager():
    """Return a clean ConversationManager with no sessions."""
    return ConversationManager(max_history=10)


@pytest.fixture
def client(fresh_manager):
    """
    Provide a (TestClient, ConversationManager) pair for API tests.

    The FastAPI lifespan is intentionally NOT invoked so no model file is
    required.  The globals `main.conversation_manager` and `main.llm_engine`
    are set directly before each test and cleaned up afterwards.
    Tests that exercise the WebSocket LLM flow must assign their own async
    generator to `main.llm_engine.stream_chat` before connecting.
    """
    main.conversation_manager = fresh_manager
    main.llm_engine = None

    # Instantiate without `with` so the lifespan (model download) is skipped.
    c = TestClient(app=main.app, raise_server_exceptions=True)

    yield c, fresh_manager

    # Teardown — reset globals so tests don't bleed state into each other.
    main.conversation_manager = None
    main.llm_engine = None
