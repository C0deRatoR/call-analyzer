from sentiment_analyzer import EnhancedSentimentAnalyzer

def test_sentiment_positive():
    analyzer = EnhancedSentimentAnalyzer()
    result = analyzer.analyze_sentiment("This is a fantastic tool! I love it! Thank you.")
    assert result['vader_scores']['compound'] > 0.5
    assert result['sentiment_label'] == 'very_positive'
    assert 'positive_language' in result['emotional_indicators']

def test_sentiment_negative():
    analyzer = EnhancedSentimentAnalyzer()
    result = analyzer.analyze_sentiment("This is terrible, I hate the delay and awful service.")
    assert result['vader_scores']['compound'] < -0.5
    assert result['sentiment_label'] == 'very_negative'
    assert 'negative_language' in result['emotional_indicators']

def test_sentiment_neutral():
    analyzer = EnhancedSentimentAnalyzer()
    result = analyzer.analyze_sentiment("The call was completed on time, just passing by.")
    assert -0.5 <= result['vader_scores']['compound'] <= 0.5
