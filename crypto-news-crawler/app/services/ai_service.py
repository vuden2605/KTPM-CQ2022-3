"""
app/services/ai_service.py

Service for AI-powered analysis (sentiment, prediction, etc).
(Part 3: AI Analysis & Insights)
"""

import os
import json
from typing import Dict, List, Optional

try:
    from google import genai
except ImportError:  # pragma: no cover - optional dependency
    genai = None

try:
    import httpx
except ImportError:
    httpx = None


class AIService:
    """Handles AI API calls for sentiment analysis, predictions, etc."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash-exp", ollama_url: Optional[str] = None, ollama_model: str = "gemma3:1b"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model
        self.ollama_url = ollama_url or os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.ollama_model = ollama_model or os.getenv("OLLAMA_MODEL", "gemma3:1b")
    
    def analyze_sentiment(self, text: str) -> Dict[str, any]:
        """Analyze sentiment of news article or social media text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dict with sentiment_label (positive/negative/neutral) and score.
        """
        # TODO: Implement OpenAI/HuggingFace API call
        # response = openai.ChatCompletion.create(
        #     model=self.model,
        #     messages=[{"role": "user", "content": f"Analyze sentiment: {text}"}]
        # )
        # return parse_sentiment(response)
        pass
    
    def predict_price_impact(
        self,
        symbol: str,
        news_sentiment: float,
        recent_news: List[str],
    ) -> Dict[str, any]:
        """Predict potential price impact based on news sentiment.
        
        Args:
            symbol: Crypto symbol (BTC, ETH, ...)
            news_sentiment: Aggregate sentiment score
            recent_news: List of recent news headlines
            
        Returns:
            Dict with prediction, confidence, etc.
        """
        # TODO: Implement ML model or AI API call
        pass
    
    def summarize_news(self, articles: List[str]) -> str:
        """Summarize a batch of news articles.
        
        Args:
            articles: List of article texts
            
        Returns:
            Concise summary.
        """
        # TODO: Implement summarization
        pass

    def _call_ollama(self, prompt: str, source_code: str) -> Optional[str]:
        """Call local Ollama API if available."""
        if not httpx:
            return None
        try:
            print(f"[AI] Calling Ollama ({self.ollama_model}) at {self.ollama_url} for {source_code}...")
            # Prefer chat with JSON formatting
            response = httpx.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.ollama_model,
                    "messages": [
                        {"role": "system", "content": "You only respond with valid JSON. No commentary, no markdown."},
                        {"role": "user", "content": prompt},
                    ],
                    "format": "json",
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 800,
                    }
                },
                timeout=90.0,
            )
            response.raise_for_status()
            data = response.json()
            text = (data.get("message", {}).get("content") or "").strip()
            if not text:
                # Fallback to generate endpoint
                gen = httpx.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": prompt,
                        "format": "json",
                        "stream": False,
                        "options": {
                            "temperature": 0.1,
                            "num_predict": 800,
                        }
                    },
                    timeout=90.0,
                )
                gen.raise_for_status()
                gdata = gen.json()
                text = (gdata.get("response") or "").strip()
            print(f"[AI] Ollama response received for {source_code}")
            return text
        except Exception as e:
            print(f"[AI] Ollama call failed: {e}")
            return None

    def generate_crawler_config(
        self,
        source_code: str,
        hints: Optional[dict] = None,
        html_samples: Optional[Dict[str, str]] = None,
        fail_info: Optional[Dict[str, str]] = None,
    ) -> Dict[str, any]:
        """Generate a crawler config for a news source using Ollama (local) or Gemini API (if available).

        - Thử Ollama trước (nếu có sẵn), sau đó thử Gemini, cuối cùng dùng hints.
        """
        base_hints = hints or {}
        # Build prompt with optional HTML context samples (truncated to keep size reasonable)
        def _clip_html(s: str, limit: int = int(os.getenv("AI_HTML_SAMPLE_LIMIT", "15000")) ) -> str:
            try:
                return s[:limit]
            except Exception:
                return s

        samples_text = ""
        if html_samples:
            list_html = html_samples.get("list")
            article_html = html_samples.get("article")
            if list_html:
                samples_text += (
                    "\nContext: List page HTML (truncated)\n"
                    "<BEGIN_HTML>\n" + _clip_html(list_html) + "\n<END_HTML>\n"
                )
            if article_html:
                samples_text += (
                    "\nContext: Article page HTML (truncated)\n"
                    "<BEGIN_HTML>\n" + _clip_html(article_html) + "\n<END_HTML>\n"
                )

        prompt = (
            "You are a JSON generator. Generate ONLY valid JSON, no explanations, no markdown.\n"
            "Task: Create crawler config for news source.\n"
            f"Source: {source_code}\n"
            f"Reference (may be incomplete): {json.dumps(base_hints)}\n"
            f"{samples_text}\n\n"
            + ("Previous attempt failed for fields: " + json.dumps(fail_info) + "\n\n" if fail_info else "") +
            "Output format (MUST be valid JSON):\n"
            "{\n"
            '  "list_url": "https://...",\n'
            '  "list_link_selector": "CSS selector",\n'
            '  "url_prefix": "https://...",\n'
            '  "article": {\n'
            '    "title_selector": "h1",\n'
            '    "content_selector": "div.content",\n'
            '    "date_selector_meta": "article:published_time",\n'
            "    \"author_selector\": \"a[href*='/author/'], a[href*='/authors/'], meta[name='author']\"\n"
            "  }\n"
            "}\n\n"
            "Constraints: selectors MUST resolve to non-empty nodes when applied to the provided HTML samples.\n"
            "Generate complete valid JSON now:"
        )

        # Try Ollama first
        ollama_text = self._call_ollama(prompt, source_code)
        if ollama_text:
            try:
                # Clean markdown code fences
                cleaned = ollama_text.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.strip("`")
                    if cleaned.lower().startswith("json"):
                        cleaned = cleaned[4:]
                    cleaned = cleaned.strip()
                
                # Try to fix common JSON issues
                # Fix missing closing brackets/quotes
                if cleaned.count("{") > cleaned.count("}"):
                    cleaned += "}" * (cleaned.count("{") - cleaned.count("}"))
                if cleaned.count("[") > cleaned.count("]"):
                    cleaned += "]" * (cleaned.count("[") - cleaned.count("]"))
                
                # Fix incomplete quotes in selectors like "meta[name='authors'"
                import re
                # Find patterns like "meta[name='xxx'" and add closing ]
                cleaned = re.sub(r'"(meta\[[^\]]+)(?<!\\)"', r'"\1]"', cleaned)

                # If still not valid, attempt to extract first JSON object substring
                try:
                    return json.loads(cleaned)
                except Exception:
                    start = cleaned.find("{")
                    end = cleaned.rfind("}")
                    if start != -1 and end != -1 and end > start:
                        snippet = cleaned[start:end+1]
                        cfg = json.loads(snippet)
                        print(f"[AI] Ollama config successfully parsed (trimmed) for {source_code}")
                        return cfg
                
                cfg = json.loads(cleaned)
                print(f"[AI] Ollama config successfully parsed for {source_code}")
                return cfg
            except Exception as e:
                print(f"[AI] Failed to parse Ollama response: {e}")
                print(f"[AI] Raw response: {ollama_text[:200]}...")

        # Try Gemini if Ollama fails
        if genai is not None and self.api_key:
            client = genai.Client(api_key=self.api_key)
            try:
                print(f"[AI] Calling Gemini ({self.model}) for {source_code}...")
                response = client.models.generate_content(
                    model=self.model,
                    contents=[prompt],
                )
                text = (response.text or "").strip()
                if text.startswith("```"):
                    text = text.strip("`")
                    if text.lower().startswith("json"):
                        text = text[4:]
                    text = text.strip()
                cfg = json.loads(text)
                print(f"[AI] Gemini ({self.model}) config fetched for {source_code}")
                return cfg
            except Exception as e:
                print(f"[AI] Gemini call failed for {source_code}: {e}")

        # Fallback to hints
        if hints:
            print(f"[AI] Using hints fallback for {source_code}")
            return hints
        
        raise RuntimeError("No AI provider available and no hints provided")

    def extract_article_fields(self, html: str, source_code: str, url: str = "") -> Optional[Dict[str, any]]:
        """Use Ollama/Gemini to extract structured fields from raw HTML.

        Returns minimal dict, e.g.: {"author": "Name"}
        Only author is guaranteed; other fields may be added later.
        """
        # Build concise prompt with truncated HTML
        def _clip_html(s: str, limit: int = int(os.getenv("AI_HTML_SAMPLE_LIMIT", "12000")) ) -> str:
            try:
                return s[:limit]
            except Exception:
                return s

        prompt = (
            "You only respond with valid JSON. No commentary, no markdown.\n"
            "Task: From the provided HTML of a news article, extract fields. Focus on author.\n"
            f"Source: {source_code}\n"
            f"URL: {url}\n\n"
            "How to find author (try in order):\n"
            "1) Visible byline links: anchors like a[href*='/author/'] or a[href*='/authors/']\n"
            "2) Meta tags: name=author, name=authors, property=article:author, name=parsely-author, name=sailthru.author, name=twitter:creator (@handle)\n"
            "3) JSON-LD: author/creator/contributor objects or lists, @graph nodes of type Person with name\n"
            "4) Byline text: phrases starting with 'By ' or 'Written by' near the title or article header\n\n"
            "Output JSON schema (include only fields you can determine):\n"
            "{\n  \"author\": \"Full name(s) comma-separated\"\n}\n\n"
            "HTML (truncated):\n<BEGIN_HTML>\n" + _clip_html(html) + "\n<END_HTML>\n\n"
            "Return JSON now."
        )

        # Prefer Ollama
        text = self._call_ollama(prompt, source_code)
        parsed: Optional[Dict[str, any]] = None
        if text:
            try:
                cleaned = text.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.strip("`")
                    if cleaned.lower().startswith("json"):
                        cleaned = cleaned[4:]
                    cleaned = cleaned.strip()
                parsed = json.loads(cleaned)
            except Exception:
                parsed = None

        # Try Gemini if Ollama absent or failed
        if parsed is None and genai is not None and self.api_key:
            try:
                client = genai.Client(api_key=self.api_key)
                response = client.models.generate_content(model=self.model, contents=[prompt])
                text2 = (response.text or "").strip()
                if text2.startswith("```"):
                    text2 = text2.strip("`")
                    if text2.lower().startswith("json"):
                        text2 = text2[4:]
                    text2 = text2.strip()
                parsed = json.loads(text2)
            except Exception:
                parsed = None

        return parsed


def get_ai_service() -> AIService:
    """Factory function to create AIService instance."""
    # Could load API key from config or environment
    return AIService()
