"""
app/services/sentiment_analyzer.py

Sentiment Analysis service using FinBERT (financial sentiment) with fallback to VADER.
FinBERT provides domain-specific sentiment for finance/news; if unavailable, we
fallback to VADER to avoid breaking functionality.
"""

from typing import Dict

# --- Try to use FinBERT (HuggingFace) ---
_FINBERT_AVAILABLE = False
_finbert_model = None
_finbert_tokenizer = None

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch

    _FINBERT_MODEL_NAME = "yiyanghkust/finbert-tone"
    _finbert_tokenizer = AutoTokenizer.from_pretrained(_FINBERT_MODEL_NAME)
    _finbert_model = AutoModelForSequenceClassification.from_pretrained(_FINBERT_MODEL_NAME)
    _finbert_model.eval()
    _FINBERT_AVAILABLE = True
except Exception as e:
    # FinBERT unavailable; will fallback to VADER
    _FINBERT_AVAILABLE = False
    _finbert_model = None
    _finbert_tokenizer = None

# --- VADER fallback ---
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk

try:
    nltk.data.find('sentiment/vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon', quiet=True)

_vader = SentimentIntensityAnalyzer()


def _analyze_sentiment_vader(text: str) -> Dict[str, any]:
    """VADER-based sentiment analysis (fallback)."""
    if not text or len(text.strip()) == 0:
        return {
            'score': 0.0,
            'label': 'neutral',
            'compound': 0.0,
            'positive': 0.0,
            'negative': 0.0,
            'neutral': 1.0,
            'confidence': 0.0
        }

    scores = _vader.polarity_scores(text)
    compound = scores['compound']
    if compound >= 0.05:
        label = 'positive'
        confidence = scores['pos']
    elif compound <= -0.05:
        label = 'negative'
        confidence = scores['neg']
    else:
        label = 'neutral'
        confidence = scores['neu']
    normalized_score = (compound + 1) / 2
    return {
        'score': normalized_score,
        'label': label,
        'compound': compound,
        'positive': scores['pos'],
        'negative': scores['neg'],
        'neutral': scores['neu'],
        'confidence': confidence
    }


def _analyze_sentiment_finbert(text: str) -> Dict[str, any]:
    """FinBERT-based sentiment analysis for financial/news text."""
    if not text or len(text.strip()) == 0:
        return {
            'score': 0.0,
            'label': 'neutral',
            'compound': 0.0,
            'positive': 0.0,
            'negative': 0.0,
            'neutral': 1.0,
            'confidence': 0.0
        }

    assert _finbert_model is not None and _finbert_tokenizer is not None
    with torch.no_grad():
        inputs = _finbert_tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        outputs = _finbert_model(**inputs)
        logits = outputs.logits  # shape [1, 3]
        probs = torch.softmax(logits, dim=1)[0].tolist()

    # Map probs to labels via id2label
    id2label = {i: _finbert_model.config.id2label[i].lower() for i in range(len(probs))}
    distro = {id2label[i]: probs[i] for i in range(len(probs))}
    pos = float(distro.get('positive', 0.0))
    neg = float(distro.get('negative', 0.0))
    neu = float(distro.get('neutral', 0.0))

    # Predicted label & confidence (max prob)
    label = max(distro, key=distro.get)
    confidence = float(distro[label])

    # Derive compound in [-1,1] from (pos - neg), then normalize to [0,1]
    compound = pos - neg
    normalized_score = (compound + 1) / 2

    return {
        'score': normalized_score,
        'label': label,
        'compound': compound,
        'positive': pos,
        'negative': neg,
        'neutral': neu,
        'confidence': confidence
    }


def analyze_sentiment(text: str) -> Dict[str, any]:
    """Public API: use FinBERT when available, else fallback to VADER."""
    if _FINBERT_AVAILABLE:
        try:
            return _analyze_sentiment_finbert(text)
        except Exception:
            # In case of runtime error, fallback silently
            return _analyze_sentiment_vader(text)
    else:
        return _analyze_sentiment_vader(text)


def analyze_news_sentiment(title: str, content: str = None, summary: str = None) -> Dict[str, any]:
    """
    Analyze sentiment of a news article (title + content + summary)
    
    Args:
        title: News title (required)
        content: News content (optional)
        summary: News summary (optional)
    
    Returns:
        Sentiment analysis result
    """
    
    # Combine title, summary, and content for better analysis
    texts = [title]
    if summary:
        texts.append(summary)
    if content:
        texts.append(content)
    
    combined_text = " ".join(texts)
    return analyze_sentiment(combined_text)


def sentiment_model_name() -> str:
    """Return the sentiment model name currently in use."""
    return "FinBERT" if _FINBERT_AVAILABLE else "VADER"


def batch_analyze_sentiment(news_items: list) -> list:
    """
    Analyze sentiment for multiple news items
    
    Args:
        news_items: List of news dictionaries with 'title', 'content', 'summary'
    
    Returns:
        List of news items with added 'sentiment_label' and 'sentiment_score'
    """
    
    for item in news_items:
        result = analyze_news_sentiment(
            title=item.get('title', ''),
            content=item.get('content', ''),
            summary=item.get('summary', '')
        )
        
        item['sentiment_score'] = result['score']
        item['sentiment_label'] = result['label']
    
    return news_items


# Test sentiment analyzer
if __name__ == "__main__":
    # Test cases
    test_texts = [
        "Bitcoin Reaches New All-Time High",
        "Crypto Market Crashes Amid Regulatory Concerns",
        "Ethereum Foundation Announces New Upgrade",
        "Bitcoin Faces Pressure from Bearish Sentiment",
        "SEC Approves First Bitcoin Futures ETF",
    ]
    
    print("=" * 70)
    print("SENTIMENT ANALYSIS TEST")
    print("=" * 70)
    
    for text in test_texts:
        result = analyze_sentiment(text)
        print(f"\nText: {text}")
        print(f"  Label: {result['label'].upper()}")
        print(f"  Score: {result['score']:.2f}")
        print(f"  Compound: {result['compound']:.3f}")
        print(f"  Confidence: {result['confidence']:.2f}")
