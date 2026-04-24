"""
Pytest configuration and shared fixtures
"""

import pytest
import asyncio
from typing import AsyncGenerator


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def add_asyncio_marker(request):
    """Automatically add asyncio marker to async tests"""
    if asyncio.iscoroutinefunction(request.function):
        request.keywords["asyncio"] = True