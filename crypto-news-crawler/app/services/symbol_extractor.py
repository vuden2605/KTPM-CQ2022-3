"""
app/services/symbol_extractor.py

Service để trích xuất các cryptocurrency symbols được nhắc đến trong bài viết.
"""

import re
from typing import List, Set, Dict, Optional
from app.core.storage import db_session, BACKEND


# Mapping tên thông dụng -> symbol
CRYPTO_ALIASES = {
    "bitcoin": "BTC",
    "btc": "BTC",
    "ethereum": "ETH",
    "ether": "ETH",
    "eth": "ETH",
    "ripple": "XRP",
    "xrp": "XRP",
    "cardano": "ADA",
    "ada": "ADA",
    "solana": "SOL",
    "sol": "SOL",
    "polkadot": "DOT",
    "dot": "DOT",
    "dogecoin": "DOGE",
    "doge": "DOGE",
    "avalanche": "AVAX",
    "avax": "AVAX",
    "polygon": "MATIC",
    "matic": "MATIC",
    "chainlink": "LINK",
    "link": "LINK",
    "litecoin": "LTC",
    "ltc": "LTC",
    "uniswap": "UNI",
    "uni": "UNI",
    "binance coin": "BNB",
    "bnb": "BNB",
    "stellar": "XLM",
    "xlm": "XLM",
    "cosmos": "ATOM",
    "atom": "ATOM",
    "monero": "XMR",
    "xmr": "XMR",
    "tron": "TRX",
    "trx": "TRX",
    "toncoin": "TON",
    "ton": "TON",
    "shiba inu": "SHIB",
    "shib": "SHIB",
}


class SymbolExtractor:
    """Extract cryptocurrency symbols from article text."""
    
    def __init__(self):
        self._cache: Optional[Dict[str, Set[str]]] = None
    
    def _load_symbols_from_db(self) -> Dict[str, Set[str]]:
        """Load active symbols from database and cache them.
        
        Returns:
            Dict with keys:
                - 'symbols': Set of full trading pairs (BTCUSDT, ETHUSDT)
                - 'bases': Set of base assets (BTC, ETH)
        """
        if self._cache is not None:
            return self._cache
        
        try:
            with db_session() as db:
                if BACKEND == "sql":
                    try:
                        # Import lazily to avoid hard dependency when SQL backend is disabled
                        from app.models import Symbol  # type: ignore
                        rows = db.query(Symbol).filter(Symbol.IsActive == True).all()
                        symbols = {r.Symbol.upper() for r in rows if getattr(r, "Symbol", None)}
                        bases = {r.BaseAsset.upper() for r in rows if getattr(r, "BaseAsset", None)}
                    except Exception as ie:
                        raise RuntimeError(f"SQL backend unavailable: {ie}")
                else:
                    # Robust Mongo collection resolution: prefer get_collection, then key access, then attribute
                    coll = None
                    try:
                        if hasattr(db, "get_collection"):
                            coll = db.get_collection("Symbols")
                    except Exception:
                        coll = None
                    if coll is None:
                        try:
                            coll = db["Symbols"]
                        except Exception:
                            coll = None
                    if coll is None:
                        coll = getattr(db, "Symbols", None)
                    docs = list(coll.find({"IsActive": True})) if coll else []
                    symbols = {str(d.get("Symbol", "")).upper() for d in docs if d.get("Symbol")}
                    bases = {str(d.get("BaseAsset", "")).upper() for d in docs if d.get("BaseAsset")}

                self._cache = {
                    "symbols": symbols,
                    "bases": bases
                }
        except Exception as e:
            print(f"[SymbolExtractor] Failed to load from DB: {e}")
            # Fallback to common crypto bases
            self._cache = {
                "symbols": set(),
                "bases": {"BTC", "ETH", "XRP", "ADA", "SOL", "DOT", "DOGE", "AVAX", 
                         "MATIC", "LINK", "LTC", "UNI", "BNB", "XLM", "ATOM", "XMR", 
                         "TRX", "TON", "SHIB"}
            }
        
        return self._cache
    
    def map_to_trading_pairs(self, base_symbols: List[str], quote_currency: str = "USDT") -> Dict[str, str]:
        """Map base symbols to full trading pairs.
        
        Args:
            base_symbols: List of base symbols (e.g., ['BTC', 'ETH'])
            quote_currency: Quote currency to append (default: USDT)
            
        Returns:
            Dict mapping base to trading pair (e.g., {'BTC': 'BTCUSDT', 'ETH': 'ETHUSDT'})
        """
        if not base_symbols:
            return {}
        
        mapping = {}
        symbol_data = self._load_symbols_from_db()
        valid_symbols = symbol_data["symbols"]
        
        for base in base_symbols:
            base = base.upper()
            # Try với quote currency được chỉ định
            trading_pair = f"{base}{quote_currency}"
            if trading_pair in valid_symbols:
                mapping[base] = trading_pair
            else:
                # Fallback: thử các quote currencies phổ biến
                for quote in ["USDT", "USDC", "BUSD", "USD"]:
                    pair = f"{base}{quote}"
                    if pair in valid_symbols:
                        mapping[base] = pair
                        break
                else:
                    # Nếu không tìm thấy trong DB, dùng default
                    mapping[base] = f"{base}{quote_currency}"
        
        return mapping
    
    def extract_symbols(self, text: str, max_results: int = 10) -> List[str]:
        """Extract cryptocurrency symbols from text.
        
        Args:
            text: Combined title + content text
            max_results: Maximum number of symbols to return
            
        Returns:
            List of unique symbol strings (e.g., ['BTC', 'ETH', 'SOL'])
        """
        if not text:
            return []
        
        found_symbols: Set[str] = set()
        text_lower = text.lower()
        text_upper = text.upper()
        
        # Load valid symbols from DB
        symbol_data = self._load_symbols_from_db()
        valid_bases = symbol_data["bases"]
        valid_symbols = symbol_data["symbols"]
        
        # Pattern 1: $SYMBOL format (e.g., $BTC, $ETH)
        # Tìm $XXX với 2-10 ký tự chữ hoa
        for match in re.finditer(r'\$([A-Z]{2,10})\b', text_upper):
            sym = match.group(1)
            if sym in valid_bases:
                found_symbols.add(sym)
        
        # Pattern 2: Standalone crypto codes (e.g., BTC, ETH)
        # Tìm từ viết hoa 2-10 ký tự, không phải đầu câu
        for match in re.finditer(r'(?<![A-Z])\b([A-Z]{2,10})\b(?![A-Z])', text):
            sym = match.group(1)
            # Kiểm tra không phải từ thông dụng tiếng Anh
            if sym in valid_bases and sym not in {"US", "UK", "USA", "CEO", "CTO", "CFO", "API", "USD", "EUR"}:
                found_symbols.add(sym)
        
        # Pattern 3: Full crypto names (e.g., Bitcoin, Ethereum)
        # Tìm tên tiền mã hóa phổ biến
        for alias, symbol in CRYPTO_ALIASES.items():
            # Dùng word boundary để tránh match một phần từ
            pattern = r'\b' + re.escape(alias) + r'\b'
            if re.search(pattern, text_lower):
                if symbol in valid_bases:
                    found_symbols.add(symbol)
        
        # Pattern 4: Trading pairs (e.g., BTC/USD, BTC-USD, BTCUSDT)
        for match in re.finditer(r'\b([A-Z]{2,10})[\-/]?USD[T]?\b', text_upper):
            base = match.group(1)
            if base in valid_bases:
                found_symbols.add(base)
        
        # Sắp xếp theo thứ tự xuất hiện trong text (ưu tiên symbols xuất hiện trước)
        # và giới hạn số lượng
        result = []
        for sym in found_symbols:
            if len(result) >= max_results:
                break
            result.append(sym)
        
        return sorted(result)  # Sort alphabetically for consistency
    
    def extract_with_trading_pairs(self, text: str, max_results: int = 10, quote_currency: str = "USDT") -> Dict[str, List[str]]:
        """Extract symbols and map to trading pairs.
        
        Args:
            text: Combined title + content text
            max_results: Maximum number of symbols to return
            quote_currency: Quote currency for trading pairs (default: USDT)
            
        Returns:
            Dict with 'symbols' (base assets) and 'trading_pairs' (full pairs)
            Example: {
                'symbols': ['BTC', 'ETH', 'SOL'],
                'trading_pairs': ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
            }
        """
        base_symbols = self.extract_symbols(text, max_results)
        if not base_symbols:
            return {"symbols": [], "trading_pairs": []}
        
        pair_mapping = self.map_to_trading_pairs(base_symbols, quote_currency)
        trading_pairs = [pair_mapping.get(sym, f"{sym}{quote_currency}") for sym in base_symbols]
        
        return {
            "symbols": base_symbols,
            "trading_pairs": trading_pairs
        }


# Singleton instance
_symbol_extractor: Optional[SymbolExtractor] = None


def get_symbol_extractor() -> SymbolExtractor:
    """Factory function to get SymbolExtractor singleton instance."""
    global _symbol_extractor
    if _symbol_extractor is None:
        _symbol_extractor = SymbolExtractor()
    return _symbol_extractor


def extract_symbols_from_article(title: str, content: str, max_results: int = 10, include_trading_pairs: bool = False, quote_currency: str = "USDT"):
    """Convenience function to extract symbols from article.
    
    Args:
        title: Article title
        content: Article content
        max_results: Maximum number of symbols to return
        include_trading_pairs: If True, return dict with symbols and trading_pairs
        quote_currency: Quote currency for trading pairs (default: USDT)
        
    Returns:
        If include_trading_pairs=False: List of unique symbol strings
        If include_trading_pairs=True: Dict with 'symbols' and 'trading_pairs'
    """
    extractor = get_symbol_extractor()
    combined_text = f"{title}\n\n{content}"
    
    if include_trading_pairs:
        return extractor.extract_with_trading_pairs(combined_text, max_results=max_results, quote_currency=quote_currency)
    else:
        return extractor.extract_symbols(combined_text, max_results=max_results)
