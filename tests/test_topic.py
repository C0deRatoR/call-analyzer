import pytest
from topic_extractor import extract_keywords

@pytest.fixture
def mock_keybert(monkeypatch):
    class MockModel:
        def extract_keywords(self, text, **kwargs):
            return [("important concept", 0.9), ("keyword", 0.8)]
    monkeypatch.setattr('topic_extractor._get_model', lambda: MockModel())

def test_extract_keywords_mocked(mock_keybert):
    result = extract_keywords("This is a test transcript with a keyword and an important concept.")
    assert "important concept" in result["top_keywords"]
    assert "keyword" in result["top_keywords"]
    assert result["method"] == "keybert"

def test_extract_keywords_empty():
    result = extract_keywords("   ")
    assert result["keywords"] == []
    assert result["method"] == "none"

def test_fallback_keywords(monkeypatch):
    # Force _get_model to return None to trigger fallback
    monkeypatch.setattr('topic_extractor._get_model', lambda: None)
    result = extract_keywords("transcript system testing meaningful information server error issue problem")
    assert result["method"] == "tfidf_fallback"
    assert len(result["keywords"]) > 0
