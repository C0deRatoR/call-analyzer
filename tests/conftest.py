import os
import sys

# Set mock API key for testing before any app imports
os.environ["API_KEY"] = "mock_api_key"
import pytest

# Add src to the path so test modules can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from app import create_app

@pytest.fixture
def test_client():
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    
    with app.test_client() as client:
        yield client
