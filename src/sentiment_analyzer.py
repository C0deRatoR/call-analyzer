import logging
from typing import Dict, List, Any
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re

logger = logging.getLogger(__name__)

class EnhancedSentimentAnalyzer:
    """Enhanced sentiment analysis combining VADER scores with text analysis."""
    
    def __init__(self):
        self.vader_analyzer = SentimentIntensityAnalyzer()
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Perform comprehensive sentiment analysis on text.
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary containing VADER scores and interpretation
        """
        try:
            # Get VADER sentiment scores
            vader_scores = self.vader_analyzer.polarity_scores(text)
            
            # Interpret the compound score
            sentiment_label = self._interpret_compound_score(vader_scores['compound'])
            
            # Analyze emotional indicators
            emotional_indicators = self._extract_emotional_indicators(text)
            
            # Calculate confidence level
            confidence = self._calculate_confidence(vader_scores)
            
            return {
                'vader_scores': {
                    'positive': round(vader_scores['pos'], 3),
                    'negative': round(vader_scores['neg'], 3), 
                    'neutral': round(vader_scores['neu'], 3),
                    'compound': round(vader_scores['compound'], 3)
                },
                'sentiment_label': sentiment_label,
                'confidence': confidence,
                'emotional_indicators': emotional_indicators,
                'summary': self._generate_sentiment_summary(vader_scores, sentiment_label, emotional_indicators)
            }
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {
                'error': f"Sentiment analysis failed: {str(e)}",
                'vader_scores': {'positive': 0, 'negative': 0, 'neutral': 1, 'compound': 0},
                'sentiment_label': 'neutral',
                'confidence': 'low'
            }
    
    def _interpret_compound_score(self, compound_score: float) -> str:
        """Interpret VADER compound score into sentiment categories."""
        if compound_score >= 0.5:
            return 'very_positive'
        elif compound_score >= 0.1:
            return 'positive'
        elif compound_score > -0.1:
            return 'neutral'
        elif compound_score > -0.5:
            return 'negative'
        else:
            return 'very_negative'
    
    def _extract_emotional_indicators(self, text: str) -> List[str]:
        """Extract emotional indicators from text."""
        indicators = []
        
        # Positive indicators
        positive_patterns = [
            r'\b(great|excellent|wonderful|amazing|fantastic|perfect|love|happy|excited|pleased)\b',
            r'\b(thank you|thanks|appreciate|grateful)\b',
            r'\b(yes|absolutely|definitely|certainly|sure)\b'
        ]
        
        # Negative indicators  
        negative_patterns = [
            r'\b(terrible|awful|horrible|frustrated|angry|upset|disappointed|worried|concerned)\b',
            r'\b(problem|issue|trouble|difficult|hard|challenging)\b',
            r'\b(no|never|nothing|nobody|nowhere)\b'
        ]
        
        # Question/uncertainty indicators
        question_patterns = [
            r'\b(confused|uncertain|unsure|maybe|perhaps|possibly)\b',
            r'\?'
        ]
        
        text_lower = text.lower()
        
        for pattern in positive_patterns:
            if re.search(pattern, text_lower):
                indicators.append('positive_language')
                break
                
        for pattern in negative_patterns:
            if re.search(pattern, text_lower):
                indicators.append('negative_language')
                break
                
        for pattern in question_patterns:
            if re.search(pattern, text_lower):
                indicators.append('uncertainty')
                break
        
        return indicators
    
    def _calculate_confidence(self, vader_scores: Dict[str, float]) -> str:
        """Calculate confidence level based on score distribution."""
        compound_abs = abs(vader_scores['compound'])
        
        if compound_abs >= 0.5:
            return 'high'
        elif compound_abs >= 0.1:
            return 'medium'
        else:
            return 'low'
    
    def _generate_sentiment_summary(self, vader_scores: Dict[str, float], 
                                  sentiment_label: str, indicators: List[str]) -> str:
        """Generate a human-readable summary of sentiment analysis."""
        compound = vader_scores['compound']
        
        # Base sentiment description
        sentiment_descriptions = {
            'very_positive': 'Very positive sentiment detected',
            'positive': 'Positive sentiment detected',
            'neutral': 'Neutral sentiment detected', 
            'negative': 'Negative sentiment detected',
            'very_negative': 'Very negative sentiment detected'
        }
        
        summary = sentiment_descriptions.get(sentiment_label, 'Mixed sentiment detected')
        
        # Add score details
        summary += f" (compound score: {compound:.3f})"
        
        # Add emotional indicators
        if indicators:
            indicator_text = ', '.join(indicators)
            summary += f". Emotional indicators: {indicator_text}"
        
        return summary
