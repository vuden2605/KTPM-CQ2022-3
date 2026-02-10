"""
BaseNewsCrawler: Template Method pattern for news crawlers.

Subclasses provide source-specific URL discovery and (optionally) extraction tweaks,
while the base class handles config resolution (cache → AI → default), extraction,
normalization, sentiment analysis, and DB storage.
"""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from datetime import datetime
from urllib.parse import urljoin
import re

import trafilatura
import dateparser
from bs4 import BeautifulSoup
try:
    import feedparser  # RSS/Atom parser
except Exception:
    feedparser = None

from app.core.fetcher import fetch_html
from app.core.normalizer import normalize_article
from app.core.storage import db_session, get_source_by_code, save_article as db_save_article
from app.services.ai_service import get_ai_service
from app.services.sentiment_analyzer import analyze_news_sentiment, sentiment_model_name
from app.services.symbol_extractor import extract_symbols_from_article


class BaseNewsCrawler:
    """Template Method base class for news crawlers.

    Subclasses must provide:
    - `source_code`: short identifier matching NewsSources.Code
    - `base_url`: site base URL
    - `default_config`: dict with discovery/extraction settings
    - `cache_filename`: JSON filename stored next to this module
    """

    def __init__(
        self,
        source_code: str,
        base_url: str,
        default_config: Dict,
        cache_filename: str,
    ) -> None:
        self.source_code = source_code
        self.base_url = base_url.rstrip("/")
        self.default_config = default_config or {}
        self._cache_path = (Path(__file__).resolve().parent / cache_filename)

    def _is_valid_config(self, cfg: Optional[Dict]) -> bool:
        if not isinstance(cfg, dict):
            return False
        # Basic required keys
        if not cfg.get("list_url"):
            return False
        art = cfg.get("article")
        if not isinstance(art, dict):
            return False
        return True

    def _sanitize_config(self, cfg: Dict) -> Dict:
        cfg = dict(cfg or {})
        art = dict(cfg.get("article") or {})
        # Normalize simple string fields
        for key in [
            "title_selector",
            "content_selector",
            "date_selector_meta",
            "author_selector",
        ]:
            val = art.get(key)
            if isinstance(val, str):
                art[key] = val.strip()
        cfg["article"] = art
        # Ensure list_url and url_prefix
        if isinstance(cfg.get("list_url"), str):
            cfg["list_url"] = cfg["list_url"].strip()
        if isinstance(cfg.get("url_prefix"), str):
            cfg["url_prefix"] = cfg["url_prefix"].strip()
        return cfg

    def _load_cached_config(self) -> Optional[Dict]:
        try:
            if self._cache_path.exists():
                with open(self._cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            return None
        return None

    def _save_cached_config(self, cfg: Dict) -> None:
        try:
            with open(self._cache_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def get_config(self) -> Dict:
        # 1) Load cached
        cfg = self._load_cached_config()
        if self._is_valid_config(cfg):
            return self._sanitize_config(cfg)  # type: ignore[arg-type]
        # 2) Optionally generate via AI (Ollama/Gemini) when enabled
        if os.getenv("ENABLE_AI_CONFIG", "0") == "1":
            try:
                html_samples: Dict[str, str] = {}
                # Try to fetch list page HTML using default config
                list_url = (self.default_config or {}).get("list_url") or self.base_url
                # Allow overriding list_url via environment when you want to lock RSS
                fixed_list_url = os.getenv("AI_CONFIG_RSS_URL") or None
                rss_text = None
                try:
                    html_samples["list"] = fetch_html(list_url)
                except Exception:
                    pass
                # Try to fetch one candidate article HTML (via feed if available)
                sample_article_html = None
                try:
                    sample_url = None
                    feed_source = fixed_list_url or list_url
                    if feedparser is not None and feed_source:
                        feed = feedparser.parse(feed_source)
                        if hasattr(feed, "entries") and feed.entries:
                            sample_url = getattr(feed.entries[0], "link", None) or getattr(feed.entries[0], "id", None)
                        # Capture raw RSS text if feed_source is RSS
                        try:
                            # If list fetch succeeded and is XML, reuse it as RSS text
                            if html_samples.get("list"):
                                rss_text = html_samples["list"]
                        except Exception:
                            rss_text = None
                    # Fallback: simple anchor discovery
                    if not sample_url:
                        shtml = html_samples.get("list") or ""
                        soup_list = BeautifulSoup(shtml, "lxml") if shtml else None
                        if soup_list:
                            for a in soup_list.find_all("a", href=True):
                                href = a["href"]
                                full = href if href.startswith("http") else urljoin((self.default_config or {}).get("url_prefix") or self.base_url, href)
                                if full.startswith(self.base_url) and any(seg in full for seg in ["/news/", "/world/", "/business/", "/markets/", "/technology/"]):
                                    sample_url = full
                                    break
                    if sample_url:
                        sample_article_html = fetch_html(sample_url)
                except Exception:
                    sample_article_html = None
                if sample_article_html:
                    html_samples["article"] = sample_article_html

                ai = get_ai_service()
                cfg_ai = ai.generate_crawler_config(
                    source_code=self.source_code,
                    hints=self.default_config,
                    html_samples=(html_samples or None),
                )
                if self._is_valid_config(cfg_ai):
                    # By default, keep discovery URLs fixed and let AI only refine 'article' fields.
                    # Set ALLOW_AI_LIST_URL=1 or ALLOW_AI_URL_PREFIX=1 to let AI override them.
                    lock_list_url = os.getenv("ALLOW_AI_LIST_URL", "0") != "1"
                    lock_url_prefix = os.getenv("ALLOW_AI_URL_PREFIX", "0") != "1"

                    # Use defaults for locked fields; if missing in defaults, keep AI values.
                    if isinstance(cfg_ai, dict):
                        if lock_list_url and isinstance((self.default_config or {}).get("list_url"), str):
                            cfg_ai["list_url"] = (self.default_config or {}).get("list_url")
                        if lock_url_prefix and isinstance((self.default_config or {}).get("url_prefix"), str):
                            cfg_ai["url_prefix"] = (self.default_config or {}).get("url_prefix")

                    cfg_ai = self._sanitize_config(cfg_ai)
                    self._save_cached_config(cfg_ai)
                    return cfg_ai
            except Exception as e:
                print(f"[Config] AI config generation failed for {self.source_code}: {e}")

        # 3) Fallback to default
        clean_default = self._sanitize_config(self.default_config)
        self._save_cached_config(clean_default)
        return clean_default

    # ---------- URL discovery (override if needed) ----------
    def discover_urls_via_feed(self, list_url: str) -> Optional[List[str]]:
        """Discover article URLs using feedparser and populate RSS metadata maps.

        Returns a de-duplicated list of URLs when feed entries are present,
        otherwise returns None to indicate no feed-based discovery.
        """
        if feedparser is None or not list_url:
            return None
        try:
            feed = feedparser.parse(list_url)
            if not hasattr(feed, "entries") or not feed.entries:
                return None

            urls: List[str] = []
            # Initialize RSS metadata maps
            self._rss_author_map = {}
            self._rss_date_map = {}
            self._rss_title_map = {}
            self._rss_summary_map = {}

            def _norm(u: Optional[str]) -> Optional[str]:
                if not u:
                    return None
                try:
                    u = u.strip()
                    if u.endswith("/"):
                        u = u[:-1]
                    u = re.sub(r"^http://", "https://", u, flags=re.IGNORECASE)
                    return u
                except Exception:
                    return u

            for entry in feed.entries:
                link = getattr(entry, "link", None) or getattr(entry, "id", None)
                if not link:
                    continue
                nlink = _norm(link) or link
                urls.append(nlink)
                # Title
                title = getattr(entry, "title", None)
                if title:
                    self._rss_title_map[nlink] = str(title).strip()
                # Summary/Description
                summary = getattr(entry, "summary", None)
                if summary:
                    self._rss_summary_map[nlink] = str(summary).strip()
                # Published date
                pub = getattr(entry, "published", None) or getattr(entry, "updated", None)
                if pub:
                    self._rss_date_map[nlink] = str(pub).strip()
                # Author(s)
                author = None
                if hasattr(entry, "author") and entry.author:
                    author = str(entry.author).strip()
                elif hasattr(entry, "authors") and entry.authors:
                    names = []
                    for a in entry.authors:
                        name = (a.get("name") if isinstance(a, dict) else None) or None
                        if name:
                            names.append(str(name).strip())
                    if names:
                        author = ", ".join(list(dict.fromkeys(names)))
                elif "dc_creator" in entry and entry["dc_creator"]:
                    author = str(entry["dc_creator"]).strip()
                if author:
                    self._rss_author_map[nlink] = author

            return list(dict.fromkeys(urls))
        except Exception:
            return None

    def get_urls(self, cfg: dict) -> List[str]:
        """Default list discovery via CSS selector.
        Subclasses can override for RSS or site-specific heuristics.
        """
        list_url = cfg.get("list_url")
        # Prefer feedparser via shared helper
        urls_via_feed = self.discover_urls_via_feed(list_url) if list_url else None
        if urls_via_feed:
            # Optional feed include/exclude filters from config
            include_patterns = (cfg.get("feed_include_patterns") or [])
            exclude_patterns = (cfg.get("feed_exclude_patterns") or [])

            def _matches_any(u: str, patterns: List[str]) -> bool:
                for p in patterns:
                    try:
                        if p and p in u:
                            return True
                    except Exception:
                        continue
                return False

            filtered = urls_via_feed
            # Apply include first (if provided)
            if include_patterns:
                filtered = [u for u in filtered if _matches_any(u, include_patterns)]
            # Apply exclude next
            if exclude_patterns:
                filtered = [u for u in filtered if not _matches_any(u, exclude_patterns)]
            return filtered

        # Fallback: fetch HTML and use selector/heuristic or XML sitemap/RSS parsing
        html = ""
        try:
            html = fetch_html(list_url)
        except Exception as e:
            print(f"[List] Fetch failed for {list_url}: {e}. Falling back to default list.")
            fallback_list = (self.default_config or {}).get("list_url") or self.base_url
            try:
                # Before fetching HTML, try feed discovery again using fallback list
                list_url = fallback_list
                urls_via_feed_fb = self.discover_urls_via_feed(list_url) if list_url else None
                if urls_via_feed_fb:
                    include_patterns = (cfg.get("feed_include_patterns") or [])
                    exclude_patterns = (cfg.get("feed_exclude_patterns") or [])

                    def _matches_any(u: str, patterns: List[str]) -> bool:
                        for p in patterns:
                            try:
                                if p and p in u:
                                    return True
                            except Exception:
                                continue
                        return False

                    filtered = urls_via_feed_fb
                    if include_patterns:
                        filtered = [u for u in filtered if _matches_any(u, include_patterns)]
                    if exclude_patterns:
                        filtered = [u for u in filtered if not _matches_any(u, exclude_patterns)]
                    return filtered

                # If feed discovery via fallback fails, fetch HTML for heuristic discovery
                html = fetch_html(fallback_list)
            except Exception as e2:
                print(f"[List] Fallback fetch failed for {fallback_list}: {e2}")
                return []

        # Try XML-aware parsing first (handles RSS/Atom and Sitemaps)
        try:
            sx = BeautifulSoup(html, "xml")
        except Exception:
            sx = None

        def _apply_patterns(urls: List[str]) -> List[str]:
            include_patterns = (cfg.get("feed_include_patterns") or [])
            exclude_patterns = (cfg.get("feed_exclude_patterns") or [])

            def _matches_any(u: str, patterns: List[str]) -> bool:
                for p in patterns:
                    try:
                        if p and p in u:
                            return True
                    except Exception:
                        continue
                return False

            filtered = urls
            if include_patterns:
                filtered = [u for u in filtered if _matches_any(u, include_patterns)]
            if exclude_patterns:
                filtered = [u for u in filtered if not _matches_any(u, exclude_patterns)]
            return filtered

        if sx is not None:
            urls_xml: List[str] = []
            try:
                # RSS (item > link) or Atom (entry > link[href])
                items = sx.find_all("item")
                entries = sx.find_all("entry")
                if items:
                    for it in items:
                        l = it.find("link")
                        if l and l.text:
                            urls_xml.append(l.text.strip())
                elif entries:
                    for en in entries:
                        l = en.find("link")
                        href = l.get("href") if l else None
                        if href:
                            urls_xml.append(href.strip())
                else:
                    # Sitemap (urlset > url > loc)
                    urlset = sx.find("urlset")
                    if urlset:
                        for u in urlset.find_all("url"):
                            loc = u.find("loc")
                            if loc and loc.text:
                                urls_xml.append(loc.text.strip())
                if urls_xml:
                    return _apply_patterns(list(dict.fromkeys(urls_xml)))
            except Exception:
                pass

        # HTML selector-based discovery
        soup = BeautifulSoup(html, "lxml")
        selector = cfg.get("list_link_selector")
        urls: List[str] = []
        # First try selector if provided
        if selector:
            for a in soup.select(selector):
                href = a.get("href")
                if not href:
                    continue
                full_url = href if href.startswith("http") else urljoin(cfg.get("url_prefix") or self.base_url, href)
                if full_url.startswith(self.base_url):
                    urls.append(full_url)
        # Fallback heuristic when selector missing or yields no URLs
        if not urls:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                full_url = href if href.startswith("http") else urljoin(self.base_url, href)
                # Accept common article path segments
                if full_url.startswith(self.base_url) and any(seg in full_url for seg in ["/news/", "/world/", "/business/", "/markets/", "/technology/"]):
                    urls.append(full_url)
        return list(set(_apply_patterns(urls)))

    # ---------- Article extraction (can be overridden) ----------
    def extract_article(self, url: str, cfg: dict) -> dict:
        # Optionally prefer RSS pubDate first for precise time
        preferred_rss_dt = None
        try:
            art_cfg = (cfg.get("article") or {})
            if art_cfg.get("prefer_rss_date") and feedparser is not None:
                list_url = (cfg.get("list_url") or "")
                if list_url:
                    feed = feedparser.parse(list_url)
                    # Try to discover a canonical URL from HTML to improve matching
                    canonical_targets: List[str] = []
                    try:
                        html_for_canonical = fetch_html(url)
                        soup_canon = BeautifulSoup(html_for_canonical, "lxml")
                        # <link rel="canonical"> and og:url
                        lcanon = soup_canon.find("link", {"rel": "canonical"})
                        if lcanon and lcanon.get("href"):
                            canonical_targets.append(str(lcanon.get("href")).strip())
                        mog = soup_canon.find("meta", {"property": "og:url"})
                        if mog and mog.get("content"):
                            canonical_targets.append(str(mog.get("content")).strip())
                    except Exception:
                        pass
                    def _norm(u: Optional[str]) -> Optional[str]:
                        if not u:
                            return None
                        try:
                            u = u.strip()
                            if u.endswith("/"):
                                u = u[:-1]
                            u = re.sub(r"^http://", "https://", u, flags=re.IGNORECASE)
                            return u
                        except Exception:
                            return u
                    def _norm_path_only(u: Optional[str]) -> Optional[str]:
                        # Normalize and drop query params for robust matching
                        if not u:
                            return None
                        try:
                            u = u.strip()
                            u = re.sub(r"^http://", "https://", u, flags=re.IGNORECASE)
                            # remove query and fragment
                            u = re.sub(r"[?#].*$", "", u)
                            if u.endswith("/"):
                                u = u[:-1]
                            return u
                        except Exception:
                            return u
                    def _id_from(u: Optional[str]) -> Optional[str]:
                        if not u:
                            return None
                        try:
                            m = re.search(r"/(\d{4,})/", u)
                            if m:
                                return m.group(1)
                            m = re.search(r"[?&]p=(\d+)", u)
                            if m:
                                return m.group(1)
                        except Exception:
                            pass
                        return None
                    norm_target = _norm(url)
                    norm_target_path = _norm_path_only(url)
                    target_id = _id_from(url)
                    # include canonical targets
                    canon_norms = list({x for x in [
                        _norm(canonical_targets[0]) if len(canonical_targets) > 0 else None,
                        _norm(canonical_targets[1]) if len(canonical_targets) > 1 else None,
                        _norm_path_only(canonical_targets[0]) if len(canonical_targets) > 0 else None,
                        _norm_path_only(canonical_targets[1]) if len(canonical_targets) > 1 else None,
                    ] if x})
                    for entry in getattr(feed, "entries", []) or []:
                        link = getattr(entry, "link", None)
                        eid = getattr(entry, "id", None)
                        guid = getattr(entry, "guid", None) if hasattr(entry, "guid") else None
                        candidates = [link, eid, guid]
                        matched = False
                        for cand in candidates:
                            nc = _norm(cand)
                            if nc and norm_target and nc == norm_target:
                                matched = True
                                break
                            # also compare path-only
                            npc = _norm_path_only(cand)
                            if npc and norm_target_path and npc == norm_target_path:
                                matched = True
                                break
                            # compare against discovered canonical URLs
                            if nc and canon_norms and nc in canon_norms:
                                matched = True
                                break
                            if npc and canon_norms and npc in canon_norms:
                                matched = True
                                break
                            cid = _id_from(cand)
                            if cid and target_id and cid == target_id:
                                matched = True
                                break
                        if matched:
                            pub = getattr(entry, "published", None) or getattr(entry, "updated", None)
                            if pub:
                                try:
                                    preferred_rss_dt = dateparser.parse(str(pub))
                                except Exception:
                                    preferred_rss_dt = None
                            break
        except Exception:
            preferred_rss_dt = None

        # Fetch HTML with resilience: handle 4xx/5xx and continue gracefully
        try:
            html = fetch_html(url)
        except Exception as e:
            print(f"[Article] Fetch failed for {url}: {e}")
            html = ""

        downloaded = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            output_format="json",
            with_metadata=True,
        )

        title = None
        content = None
        published_at = None
        author = None

        if downloaded:
            try:
                data = json.loads(downloaded)
            except Exception:
                data = {}
            title = data.get("title")
            content = data.get("text")
            date_str = data.get("date")
            if date_str:
                try:
                    # Trafilatura often provides date-only (YYYY-MM-DD); parse it,
                    # but we may later upgrade precision using meta/time/RSS if available.
                    published_at = dateparser.parse(date_str)
                except Exception:
                    published_at = None

        soup = BeautifulSoup(html, "lxml")

        # If we have a date-only time (midnight) and RSS has precise time for this URL, prefer RSS
        def _norm(u: Optional[str]) -> Optional[str]:
            if not u:
                return None
            try:
                u = u.strip()
                if u.endswith("/"):
                    u = u[:-1]
                u = re.sub(r"^http://", "https://", u, flags=re.IGNORECASE)
                return u
            except Exception:
                return u

        def _is_midnight_dt(dt: Optional[datetime]) -> bool:
            try:
                return (
                    isinstance(dt, datetime)
                    and dt.hour == 0 and dt.minute == 0 and dt.second == 0
                )
            except Exception:
                return False

        nurl = _norm(url) or url
        # Prefer already-resolved RSS datetime first if configured
        if preferred_rss_dt and not _is_midnight_dt(preferred_rss_dt):
            published_at = preferred_rss_dt
        elif (published_at is None or _is_midnight_dt(published_at)) and hasattr(self, "_rss_date_map") and isinstance(self._rss_date_map, dict):
            rss_date = self._rss_date_map.get(nurl) or self._rss_date_map.get(url)
            if rss_date:
                try:
                    ra = dateparser.parse(rss_date)
                    if ra and not _is_midnight_dt(ra):
                        published_at = ra
                except Exception:
                    pass

        # Fallback title
        if not title:
            tsel = (cfg.get("article") or {}).get("title_selector")
            tnode = soup.select_one(tsel) if tsel else soup.find("h1")
            if tnode:
                title = tnode.get_text(strip=True)
        if not title:
            # Try common meta tags
            article_cfg = (cfg.get("article") or {})
            meta_keys = article_cfg.get("title_meta_keys") or [
                ("property", "og:title"),
                ("property", "twitter:title"),
                ("name", "parsely-title"),
                ("name", "title"),
            ]
            for attr, val in meta_keys:
                m = soup.find("meta", {attr: val})
                if m and m.get("content"):
                    title = m.get("content")
                    break
        if not title:
            # Try JSON-LD
            for script in soup.find_all("script", {"type": "application/ld+json"}):
                try:
                    data = json.loads(script.string or "{}")
                except Exception:
                    continue
                items = data if isinstance(data, list) else [data]
                for it in items:
                    t = (it.get("headline") or it.get("name")) if isinstance(it, dict) else None
                    if t:
                        title = str(t).strip()
                        break
                if title:
                    break

        # Fallback content
        if not content:
            csel = (cfg.get("article") or {}).get("content_selector")
            if csel:
                nodes = soup.select(csel)
                text_parts = [n.get_text("\n", strip=True) for n in nodes if n]
                content = "\n\n".join([t for t in text_parts if t]) or None
            if not content:
                article = soup.find("article")
                if article:
                    content = article.get_text("\n", strip=True)

        # If content equals title or is too short, try better fallbacks
        def _clean_same_as_title(text: Optional[str], title_val: Optional[str]) -> Optional[str]:
            if not text:
                return None
            if title_val and text.strip() == title_val.strip():
                return None
            return text

        content = _clean_same_as_title(content, title)

        if not content or (isinstance(content, str) and len(content.strip()) < 120):
            # Try JSON-LD articleBody
            for script in soup.find_all("script", {"type": "application/ld+json"}):
                try:
                    data = json.loads(script.string or "{}")
                except Exception:
                    continue
                items = data if isinstance(data, list) else [data]
                body = None
                for it in items:
                    if isinstance(it, dict):
                        body = it.get("articleBody") or it.get("description")
                        if body:
                            break
                if body:
                    body = str(body).strip()
                    if title and body == title.strip():
                        body = None
                    if body:
                        content = body
                        break

        if not content or (isinstance(content, str) and len(content.strip()) < 120):
            # Try paragraphs under common containers
            para_selectors = (cfg.get("article") or {}).get("content_paragraph_selectors") or [
                "article p",
                "div.article-paragraphs p",
                "div.at-text p",
            ]
            paras = []
            for sel in para_selectors:
                paras.extend([
                    p.get_text(" ", strip=True)
                    for p in soup.select(sel)
                ])
            merged = "\n\n".join([t for t in paras if t])
            merged = _clean_same_as_title(merged, title)
            if merged:
                content = merged

        if not content or (isinstance(content, str) and len(content.strip()) < 80):
            # Last resort: meta description (not ideal, but better than title)
            desc_keys = (cfg.get("article") or {}).get("description_meta_keys") or [
                ("name", "description"),
                ("property", "og:description"),
                ("name", "twitter:description"),
            ]
            for attr, val in desc_keys:
                m = soup.find("meta", {attr: val})
                if m and m.get("content"):
                    desc = m.get("content").strip()
                    if title and desc == title.strip():
                        continue
                    if desc:
                        content = desc
                        break

        # Rendered HTML fallback disabled (skipping Playwright path)

        # Fallback published time or precision upgrade
        if not published_at:
            meta_name = (cfg.get("article") or {}).get("date_selector_meta")
            if meta_name:
                # Support both meta property and meta name attributes
                meta_time = soup.find("meta", {"property": meta_name}) or soup.find("meta", {"name": meta_name})
                if meta_time and meta_time.get("content"):
                    try:
                        published_at = dateparser.parse(meta_time["content"])  # type: ignore[index]
                    except Exception:
                        published_at = None
            if not published_at:
                time_tag = soup.find("time")
                if time_tag and (time_tag.get("datetime") or time_tag.get_text(strip=True)):
                    try:
                        dtval = time_tag.get("datetime") or time_tag.get_text(strip=True)
                        published_at = dateparser.parse(dtval)
                    except Exception:
                        published_at = None
            # Final fallback: use RSS pubDate/updated captured during feed discovery
            if not published_at and hasattr(self, "_rss_date_map") and isinstance(self._rss_date_map, dict):
                # Try normalized variants
                rss_date = self._rss_date_map.get(url) or self._rss_date_map.get(_norm(url))
                if rss_date:
                    try:
                        published_at = dateparser.parse(rss_date)
                    except Exception:
                        published_at = None
            # If still missing, try a live lookup in the feed to find this URL's pubDate
            if not published_at and feedparser is not None:
                list_url = (cfg.get("list_url") or "")
                if list_url:
                    try:
                        feed = feedparser.parse(list_url)
                        # Normalize helpers
                        def _norm(u: Optional[str]) -> Optional[str]:
                            if not u:
                                return None
                            try:
                                u = u.strip()
                                # drop trailing slash
                                if u.endswith("/"):
                                    u = u[:-1]
                                # unify scheme
                                u = re.sub(r"^http://", "https://", u, flags=re.IGNORECASE)
                                return u
                            except Exception:
                                return u

                        def _norm_path_only(u: Optional[str]) -> Optional[str]:
                            if not u:
                                return None
                            try:
                                u = u.strip()
                                u = re.sub(r"^http://", "https://", u, flags=re.IGNORECASE)
                                u = re.sub(r"[?#].*$", "", u)
                                if u.endswith("/"):
                                    u = u[:-1]
                                return u
                            except Exception:
                                return u

                        def _id_from(u: Optional[str]) -> Optional[str]:
                            if not u:
                                return None
                            try:
                                m = re.search(r"/(\d{4,})/", u)
                                if m:
                                    return m.group(1)
                                m = re.search(r"[?&]p=(\d+)", u)
                                if m:
                                    return m.group(1)
                            except Exception:
                                pass
                            return None

                        norm_target = _norm(url)
                        norm_target_path = _norm_path_only(url)
                        # include canonical from the already fetched page soup
                        canonical_targets: List[str] = []
                        try:
                            lcanon = soup.find("link", {"rel": "canonical"})
                            if lcanon and lcanon.get("href"):
                                canonical_targets.append(str(lcanon.get("href")).strip())
                            mog = soup.find("meta", {"property": "og:url"})
                            if mog and mog.get("content"):
                                canonical_targets.append(str(mog.get("content")).strip())
                        except Exception:
                            pass
                        canon_norms = list({x for x in [
                            _norm(canonical_targets[0]) if len(canonical_targets) > 0 else None,
                            _norm(canonical_targets[1]) if len(canonical_targets) > 1 else None,
                            _norm_path_only(canonical_targets[0]) if len(canonical_targets) > 0 else None,
                            _norm_path_only(canonical_targets[1]) if len(canonical_targets) > 1 else None,
                        ] if x})
                        target_id = _id_from(url)
                        for entry in getattr(feed, "entries", []) or []:
                            link = getattr(entry, "link", None)
                            eid = getattr(entry, "id", None)
                            guid = getattr(entry, "guid", None) if hasattr(entry, "guid") else None
                            candidates = [link, eid, guid]
                            matched = False
                            for cand in candidates:
                                nc = _norm(cand)
                                if nc and norm_target and nc == norm_target:
                                    matched = True
                                    break
                                npc = _norm_path_only(cand)
                                if npc and norm_target_path and npc == norm_target_path:
                                    matched = True
                                    break
                                if nc and canon_norms and nc in canon_norms:
                                    matched = True
                                    break
                                if npc and canon_norms and npc in canon_norms:
                                    matched = True
                                    break
                                # match by numeric id
                                cid = _id_from(cand)
                                if cid and target_id and cid == target_id:
                                    matched = True
                                    break
                            if matched:
                                pub = getattr(entry, "published", None) or getattr(entry, "updated", None)
                                if pub:
                                    try:
                                        published_at = dateparser.parse(str(pub))
                                    except Exception:
                                        published_at = None
                                break
                    except Exception:
                        pass
        else:
            # We have a published_at (likely from Trafilatura). If it looks date-only
            # (00:00:00 time), try to upgrade precision using page meta/time or RSS.
            is_midnight = False
            try:
                is_midnight = (
                    isinstance(published_at, datetime)
                    and published_at.hour == 0
                    and published_at.minute == 0
                    and published_at.second == 0
                )
            except Exception:
                is_midnight = False

            if is_midnight:
                upgraded = None
                # Prefer precise meta/time from page
                meta_name = (cfg.get("article") or {}).get("date_selector_meta")
                if meta_name:
                    meta_time = soup.find("meta", {"property": meta_name}) or soup.find("meta", {"name": meta_name})
                    if meta_time and meta_time.get("content"):
                        try:
                            upgraded = dateparser.parse(meta_time["content"])  # type: ignore[index]
                        except Exception:
                            upgraded = None
                if not upgraded:
                    time_tag = soup.find("time")
                    if time_tag and (time_tag.get("datetime") or time_tag.get_text(strip=True)):
                        try:
                            dtval = time_tag.get("datetime") or time_tag.get_text(strip=True)
                            upgraded = dateparser.parse(dtval)
                        except Exception:
                            upgraded = None
                if not upgraded:
                    # Try JSON-LD date fields
                    for script in soup.find_all("script", {"type": "application/ld+json"}):
                        try:
                            data_ld = json.loads(script.string or "{}")
                        except Exception:
                            continue
                        items_ld = data_ld if isinstance(data_ld, list) else [data_ld]
                        for it_ld in items_ld:
                            if isinstance(it_ld, dict):
                                for fld in ("datePublished", "dateCreated", "dateModified"):
                                    val = it_ld.get(fld)
                                    if val:
                                        try:
                                            upgraded = dateparser.parse(str(val))
                                        except Exception:
                                            upgraded = None
                                        break
                            if upgraded:
                                break
                        if upgraded:
                            break
                # Fallback to RSS if still not upgraded
                if not upgraded and hasattr(self, "_rss_date_map") and isinstance(self._rss_date_map, dict):
                    rss_date = self._rss_date_map.get(url)
                    if rss_date:
                        try:
                            upgraded = dateparser.parse(rss_date)
                        except Exception:
                            upgraded = None
                if upgraded and isinstance(upgraded, datetime):
                    published_at = upgraded
                elif upgraded is None and feedparser is not None:
                    # As a last resort for precision upgrade, try live feed lookup for this URL
                    list_url = (cfg.get("list_url") or "")
                    if list_url:
                        try:
                            feed = feedparser.parse(list_url)
                            # Reuse normalization and id-matching
                            def _norm(u: Optional[str]) -> Optional[str]:
                                if not u:
                                    return None
                                try:
                                    u = u.strip()
                                    if u.endswith("/"):
                                        u = u[:-1]
                                    u = re.sub(r"^http://", "https://", u, flags=re.IGNORECASE)
                                    return u
                                except Exception:
                                    return u

                            def _norm_path_only(u: Optional[str]) -> Optional[str]:
                                if not u:
                                    return None
                                try:
                                    u = u.strip()
                                    u = re.sub(r"^http://", "https://", u, flags=re.IGNORECASE)
                                    u = re.sub(r"[?#].*$", "", u)
                                    if u.endswith("/"):
                                        u = u[:-1]
                                    return u
                                except Exception:
                                    return u

                            def _id_from(u: Optional[str]) -> Optional[str]:
                                if not u:
                                    return None
                                try:
                                    m = re.search(r"/(\d{4,})/", u)
                                    if m:
                                        return m.group(1)
                                    m = re.search(r"[?&]p=(\d+)", u)
                                    if m:
                                        return m.group(1)
                                except Exception:
                                    pass
                                return None

                            norm_target = _norm(url)
                            norm_target_path = _norm_path_only(url)
                            canonical_targets: List[str] = []
                            try:
                                lcanon = soup.find("link", {"rel": "canonical"})
                                if lcanon and lcanon.get("href"):
                                    canonical_targets.append(str(lcanon.get("href")).strip())
                                mog = soup.find("meta", {"property": "og:url"})
                                if mog and mog.get("content"):
                                    canonical_targets.append(str(mog.get("content")).strip())
                            except Exception:
                                pass
                            canon_norms = list({x for x in [
                                _norm(canonical_targets[0]) if len(canonical_targets) > 0 else None,
                                _norm(canonical_targets[1]) if len(canonical_targets) > 1 else None,
                                _norm_path_only(canonical_targets[0]) if len(canonical_targets) > 0 else None,
                                _norm_path_only(canonical_targets[1]) if len(canonical_targets) > 1 else None,
                            ] if x})
                            target_id = _id_from(url)
                            for entry in getattr(feed, "entries", []) or []:
                                link = getattr(entry, "link", None)
                                eid = getattr(entry, "id", None)
                                guid = getattr(entry, "guid", None) if hasattr(entry, "guid") else None
                                candidates = [link, eid, guid]
                                matched = False
                                for cand in candidates:
                                    nc = _norm(cand)
                                    if nc and norm_target and nc == norm_target:
                                        matched = True
                                        break
                                    npc = _norm_path_only(cand)
                                    if npc and norm_target_path and npc == norm_target_path:
                                        matched = True
                                        break
                                    if nc and canon_norms and nc in canon_norms:
                                        matched = True
                                        break
                                    if npc and canon_norms and npc in canon_norms:
                                        matched = True
                                        break
                                    cid = _id_from(cand)
                                    if cid and target_id and cid == target_id:
                                        matched = True
                                        break
                                if matched:
                                    pub = getattr(entry, "published", None) or getattr(entry, "updated", None)
                                    if pub:
                                        try:
                                            upgraded = dateparser.parse(str(pub))
                                        except Exception:
                                            upgraded = None
                                    break
                        except Exception:
                            pass
                    if upgraded and isinstance(upgraded, datetime) and not _is_midnight_dt(upgraded):
                        published_at = upgraded

        # Author (optional)
        asel = (cfg.get("article") or {}).get("author_selector")
        if asel:
            anode = soup.select_one(asel)
            if anode:
                # If selector targets a meta tag, use its content attribute
                if anode.name == "meta":
                    author = anode.get("content") or anode.get_text(strip=True)
                else:
                    author = anode.get_text(strip=True)
        if not author:
            # Try common meta names/properties: author, authors, article:author, parsely-author
            art = (cfg.get("article") or {})
            name_keys = art.get("author_meta_name_keys") or ["author", "authors", "parsely-author", "sailthru.author"]
            prop_keys = art.get("author_meta_property_keys") or ["article:author"]
            ma = None
            for nk in name_keys:
                ma = soup.find("meta", {"name": nk})
                if ma:
                    break
            if not ma:
                for pk in prop_keys:
                    ma = soup.find("meta", {"property": pk})
                    if ma:
                        break
            if ma and ma.get("content"):
                author = ma["content"]  # type: ignore[index]
        if not author:
            # Try twitter:creator (may contain @handle)
            tw_key = (cfg.get("article") or {}).get("author_twitter_key") or "twitter:creator"
            tw = soup.find("meta", {"name": tw_key})
            if tw and tw.get("content"):
                handle = tw.get("content").strip()
                if handle.startswith("@"):  # remove @
                    handle = handle[1:]
                author = handle or None
        if not author:
            # Try JSON-LD author fields
            jsonld_author_fields = (cfg.get("article") or {}).get("author_jsonld_fields") or ["author", "creator", "contributor"]
            for script in soup.find_all("script", {"type": "application/ld+json"}):
                try:
                    data = json.loads(script.string or "{}")
                except Exception:
                    continue
                items = data if isinstance(data, list) else [data]
                names = []
                for it in items:
                    if not isinstance(it, dict):
                        continue
                    a = None
                    for fld in jsonld_author_fields:
                        a = it.get(fld)
                        if a:
                            break
                    if isinstance(a, dict):
                        n = a.get("name") or a.get("givenName")
                        if n:
                            names.append(str(n).strip())
                    elif isinstance(a, list):
                        for person in a:
                            if isinstance(person, dict):
                                n = person.get("name") or person.get("givenName")
                                if n:
                                    names.append(str(n).strip())
                    elif isinstance(a, str):
                        if a.strip():
                            names.append(a.strip())
                    # Check @graph for Person nodes
                    graph = it.get("@graph")
                    if isinstance(graph, list) and not names:
                        for node in graph:
                            if isinstance(node, dict):
                                t = node.get("@type")
                                tlist = t if isinstance(t, list) else [t]
                                if any((isinstance(x, str) and "Person" in x) for x in tlist):
                                    n = node.get("name") or node.get("givenName")
                                    if n:
                                        names.append(str(n).strip())
                names = [n for n in names if n]
                if names:
                    author = ", ".join(list(dict.fromkeys(names)))
                    break
        # Rendered byline extraction disabled (no Playwright fallback)

        # Optional: AI-assisted extraction when all fallbacks fail
        if not author and os.getenv("ENABLE_AI_EXTRACTION") == "1":
            try:
                ai = get_ai_service()
                fields = ai.extract_article_fields(html, self.source_code, url)
                if isinstance(fields, dict):
                    a = fields.get("author")
                    if isinstance(a, str) and a.strip():
                        author = a.strip()
            except Exception:
                pass

        # Final fallback: RSS author map if available
        if not author and hasattr(self, "_rss_author_map") and isinstance(self._rss_author_map, dict):
            author_hint = self._rss_author_map.get(url)
            if author_hint:
                author = author_hint.strip()

        # Normalize slug-like authors to title case
        if isinstance(author, str) and author and "-" in author and " " not in author:
            author = author.replace("-", " ").title()

        return {
            "title": title,
            "content": content,
            "published_at": published_at,
            "author": author,
            "language": "en",
        }

    # ---------- Orchestration ----------
    def save_article(self, url: str) -> None:
        raw_data = self.extract_article(url, self.get_config())
        if not raw_data or not raw_data.get("content"):
            print("Cannot extract article")
            return

        normalized = normalize_article(raw_data, self.source_code, url)

        # Extract symbols and attach to ExtraJson + top-level field when available
        try:
            symbols = extract_symbols_from_article(
                title=normalized.get("Title") or "",
                content=normalized.get("Content") or "",
                max_results=10,
            )
            if symbols:
                import json as _json
                # Merge into existing ExtraJson if present
                try:
                    existing = normalized.get("ExtraJson")
                    data = _json.loads(existing) if existing else {}
                    if not isinstance(data, dict):
                        data = {}
                except Exception:
                    data = {}
                data["symbols"] = symbols
                normalized["ExtraJson"] = _json.dumps(data, ensure_ascii=False)
                # Also store as top-level field for easier querying in Mongo
                normalized["Symbols"] = symbols
        except Exception:
            pass

        # Evaluate breaking news and attach to ExtraJson
        try:
            import json as _json
            title = normalized.get("Title") or ""
            content = normalized.get("Content") or ""
            pub = normalized.get("PublishedAt")
            now = datetime.utcnow()
            window_hours = int(os.getenv("BREAKING_TIME_WINDOW_HOURS", "2"))
            threshold = float(os.getenv("BREAKING_SCORE_THRESHOLD", "0.6"))

            tl = (title or "").lower()
            cl = (content or "").lower()

            score = 0.0
            reasons = []
            hard_event = False

            # Freshness
            try:
                if pub:
                    delta_sec = (now - pub).total_seconds()
                    if delta_sec <= window_hours * 3600:
                        score += 0.4
                        reasons.append("fresh")
            except Exception:
                pass

            # Keywords (title > content)
            kw_title = [
                "breaking", "just in", "urgent", "alert",
                "surge", "plunge", "spike", "tumbles", "soars",
                "hack", "exploit", "breach", "outage", "ban",
                "approved", "approval", "denied", "denial", "etf", "sec"
            ]
            kw_content = [
                "breaking", "just in", "urgent", "alert",
                "surge", "plunge", "spike", "tumbles", "soars",
                "price", "rally", "sell-off", "dump",
                "hack", "exploit", "breach", "outage", "ban",
                "approved", "approval", "denied", "denial", "etf", "sec"
            ]
            if any(k in tl for k in kw_title):
                score += 0.4
                reasons.append("keyword_title")
            elif any(k in cl for k in kw_content):
                score += 0.2
                reasons.append("keyword_content")

            # Percent move
            try:
                import re as _re
                perc = _re.search(r"(\d{1,3})\s?%", content or "")
                if perc and any(w in cl for w in ["price", "rise", "drop", "surge", "plunge", "soar", "tumble"]):
                    val = int(perc.group(1))
                    if val >= 10:
                        score += 0.4
                    elif val >= 7:
                        score += 0.3
                    reasons.append("percent_move")
            except Exception:
                pass

            # Hard events (immediate breaking)
            if any(x in cl for x in [
                "halting withdrawals", "withdrawals halted", "withdrawals paused",
                "exchange outage", "downtime", "service disruption",
                "hack", "exploit", "security breach",
                "sec approves", "sec approved", "etf approved", "etf approval",
                "sec denies", "sec denied", "etf denied"
            ]):
                hard_event = True
                reasons.append("hard_event")

            is_breaking = (score >= threshold) or hard_event

            # Merge to ExtraJson
            try:
                existing = normalized.get("ExtraJson")
                data = _json.loads(existing) if existing else {}
                if not isinstance(data, dict):
                    data = {}
            except Exception:
                data = {}
            data["isBreaking"] = bool(is_breaking)
            data["breakingScore"] = float(round(score, 3))
            if reasons:
                data["breakingReasons"] = reasons
            normalized["ExtraJson"] = _json.dumps(data, ensure_ascii=False)
        except Exception:
            pass

        sentiment_result = analyze_news_sentiment(
            title=normalized.get("Title") or "",
            content=normalized.get("Content") or "",
            summary=normalized.get("Summary"),
        )
        normalized["SentimentScore"] = sentiment_result["score"]
        normalized["SentimentLabel"] = sentiment_result["label"]
        normalized["SentimentModel"] = sentiment_model_name()

        with db_session() as db:
            src = get_source_by_code(db, self.source_code)
            if not src:
                print(f"Source '{self.source_code}' not found in NewsSources")
                return
            news = db_save_article(db, src.Id, normalized)
            if news:
                print(
                    f"Saved article: {news.Id} | Sentiment: "
                    f"{sentiment_result['label'].upper()} ({sentiment_result['score']:.2f})"
                )
            else:
                print("Article already exists")

    def crawl_latest_articles(self) -> None:
        cfg = self.get_config()
        urls = self.get_urls(cfg)
        print(f"Found {len(urls)} article urls")
        for url in urls:
            print("Processing:", url)
            try:
                self.save_article(url)
            except Exception as e:
                print(f"[Article] Failed {url}: {e}")

    def crawl_by_date_range(self, start: datetime, end: datetime) -> None:
        """Crawl articles within a specific [start, end] datetime range.

        Default behavior:
        - Let `get_urls` discover candidate URLs (subclasses may honor the range).
        - Extract each article and save only when `published_at` falls in range.
        """
        if start > end:
            raise ValueError("start must be <= end")

        # Let subclasses optionally optimize URL discovery for ranges
        self._date_range: Tuple[datetime, datetime] = (start, end)  # type: ignore[assignment]
        try:
            cfg = self.get_config()
            urls = self.get_urls(cfg)
        finally:
            # Clean up the hint attribute to avoid side effects on future calls
            if hasattr(self, "_date_range"):
                delattr(self, "_date_range")

        print(f"Found {len(urls)} candidate urls for range {start} -> {end}")
        kept = 0
        for url in urls:
            print("Processing:", url)
            raw = self.extract_article(url, self.get_config())
            pub = raw.get("published_at")
            if isinstance(pub, str):
                try:
                    pub = dateparser.parse(pub)
                except Exception:
                    pub = None
            if not pub or not isinstance(pub, datetime):
                continue
            if start <= pub <= end:
                # persist via normal pipeline
                normalized = normalize_article(raw, self.source_code, url)
                sentiment_result = analyze_news_sentiment(
                    title=normalized.get("Title") or "",
                    content=normalized.get("Content") or "",
                    summary=normalized.get("Summary"),
                )
                normalized["SentimentScore"] = sentiment_result["score"]
                normalized["SentimentLabel"] = sentiment_result["label"]
                normalized["SentimentModel"] = sentiment_model_name()

                with db_session() as db:
                    src = get_source_by_code(db, self.source_code)
                    if not src:
                        print(f"Source '{self.source_code}' not found in NewsSources")
                        continue
                    news = db_save_article(db, src.Id, normalized)
                    if news:
                        kept += 1
                        print(
                            f"Saved article: {news.Id} | Sentiment: "
                            f"{sentiment_result['label'].upper()} ({sentiment_result['score']:.2f})"
                        )
        print(f"Done. Saved {kept} articles in range.")
