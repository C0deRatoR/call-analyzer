import pytest
from emotion_detector import detect_emotions, detect_emotions_per_turn, get_emotion_summary

class MockPipeline:
    def __call__(self, text):
        return [[
            {"label": "joy", "score": 0.8},
            {"label": "neutral", "score": 0.1},
            {"label": "sadness", "score": 0.1}
        ]]

@pytest.fixture
def mock_pipeline(monkeypatch):
    mock = MockPipeline()
    monkeypatch.setattr('emotion_detector._load_pipeline', lambda: mock)

def test_detect_emotions_mocked(mock_pipeline):
    result = detect_emotions("I am very happy today!")
    assert result["primary_emotion"] == "joy"
    assert result["confidence"] == 0.8
    assert "joy" in result["all_scores"]
    assert "neutral" in result["all_scores"]

def test_detect_emotions_per_turn_mocked(mock_pipeline):
    turns = [
        {"speaker": "A", "text": "Happy!", "start": 0, "end": 1},
        {"speaker": "B", "text": " ", "start": 1, "end": 2}  # Empty text case
    ]
    result = detect_emotions_per_turn(turns)
    assert result[0]["emotion"]["primary_emotion"] == "joy"
    assert result[1]["emotion"]["primary_emotion"] == "neutral"  # Should default to neutral

def test_get_emotion_summary(mock_pipeline):
    turns = [
        {"speaker": "A", "text": "Happy!", "start": 0, "end": 1},
        {"speaker": "B", "text": "Yay!", "start": 1, "end": 2}
    ]
    # Populate emotions
    turns = detect_emotions_per_turn(turns)
    
    summary = get_emotion_summary(turns)
    assert summary["dominant_emotion"] == "joy"
    assert summary["emotion_distribution"]["joy"] == 1.0
    assert len(summary["emotion_timeline"]) == 2
