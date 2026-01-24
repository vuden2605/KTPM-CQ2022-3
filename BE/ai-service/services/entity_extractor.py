"""
services/entity_extractor.py
Extract entities (cryptos, orgs, people) & keywords từ tin tức
"""

from typing import Dict, List

# ============================================
# CRYPTO ENTITIES
# ============================================

CRYPTO_ENTITIES = {
    'bitcoin': ['bitcoin', 'btc'],
    'ethereum': ['ethereum', 'eth', 'ether'],
    'binance': ['binance', 'bnb'],
    'tether': ['tether', 'usdt'],
    'solana': ['solana', 'sol'],
    'cardano': ['cardano', 'ada'],
    'dogecoin': ['dogecoin', 'doge'],
    'xrp': ['xrp', 'ripple'],
    'chainlink': ['chainlink', 'link'],
    'litecoin': ['litecoin', 'ltc'],
    'polkadot': ['polkadot', 'dot'],
    'avalanche': ['avalanche', 'avax'],
    'shiba': ['shiba', 'shib'],
    'polygon': ['polygon', 'matic'],
    'uniswap': ['uniswap', 'uni'],
}

ORGANIZATIONS = {
    'sec': ['sec', 'securities and exchange commission'],
    'fed': ['fed', 'federal reserve'],
    'cftc': ['cftc', 'commodity futures trading'],
    'blackrock': ['blackrock'],
    'grayscale': ['grayscale'],
    'coinbase': ['coinbase'],
    'ftx': ['ftx'],
    'binance': ['binance'],
    'fidelity': ['fidelity'],
    'microstrategy': ['microstrategy'],
    'tesla': ['tesla'],
    'paypal': ['paypal'],
}

PEOPLE = {
    'elon_musk': ['elon musk', 'musk'],
    'trump': ['trump', 'donald trump'],
    'powell': ['powell', 'jerome powell'],
    'gensler': ['gensler', 'gary gensler'],
    'cathie_wood': ['cathie wood', 'wood'],
    'sam_bankman': ['sbf', 'sam bankman', 'bankman-fried'],
    'vitalik': ['vitalik', 'buterin'],
}

# ============================================
# KEYWORDS
# ============================================

POSITIVE_KEYWORDS = [
    'approved', 'approval', 'rally', 'surge', 'soar', 'gain', 'bullish',
    'adoption', 'institutional', 'etf approved', 'breakthrough', 'partnership',
    'launch', 'upgrade', 'integration', 'invest', 'buy', 'accumulate',
    'positive', 'boom', 'spike', 'jump', 'climb', 'rise', 'all-time high',
    'ath', 'breakout', 'momentum', 'expansion', 'growth'
]

NEGATIVE_KEYWORDS = [
    'ban', 'banned', 'crash', 'plunge', 'drop', 'fall', 'bearish',
    'regulation', 'lawsuit', 'fraud', 'hack', 'exploit', 'scam',
    'reject', 'rejected', 'concern', 'risk', 'warning', 'sell-off',
    'collapse', 'dump', 'decline', 'tumble', 'slump', 'tank',
    'crackdown', 'arrest', 'investigate', 'suspend', 'halt'
]

NEUTRAL_KEYWORDS = [
    'analyst', 'predicts', 'expects', 'report', 'study', 'data',
    'interview', 'statement', 'comment', 'update', 'news', 'says',
    'according', 'source', 'plans', 'considers', 'discussing'
]

# ============================================
# EXTRACTION FUNCTIONS
# ============================================

def extract_entities(title: str, content: str = "") -> Dict[str, List[str]]:
    """Extract entities từ title + content"""
    text = (title + " " + content).lower()
    
    result = {
        'cryptos': [],
        'orgs': [],
        'people': []
    }
    
    # Extract cryptos
    for entity, patterns in CRYPTO_ENTITIES.items():
        for pattern in patterns:
            if pattern in text:
                if entity not in result['cryptos']:
                    result['cryptos'].append(entity)
                break
    
    # Extract organizations
    for entity, patterns in ORGANIZATIONS.items():
        for pattern in patterns:
            if pattern in text:
                if entity not in result['orgs']:
                    result['orgs'].append(entity)
                break
    
    # Extract people
    for entity, patterns in PEOPLE.items():
        for pattern in patterns:
            if pattern in text:
                if entity not in result['people']:
                    result['people'].append(entity)
                break
    
    return result


def extract_keywords(title: str, content: str = "") -> Dict[str, List[str]]:
    """Extract keywords (positive/negative/neutral)"""
    text = (title + " " + content).lower()
    
    result = {
        'positive': [],
        'negative': [],
        'neutral': []
    }
    
    # Extract positive keywords
    for keyword in POSITIVE_KEYWORDS:
        if keyword in text:
            result['positive'].append(keyword)
    
    # Extract negative keywords
    for keyword in NEGATIVE_KEYWORDS:
        if keyword in text:
            result['negative'].append(keyword)
    
    # Extract neutral keywords
    for keyword in NEUTRAL_KEYWORDS:
        if keyword in text:
            result['neutral'].append(keyword)
    
    return result