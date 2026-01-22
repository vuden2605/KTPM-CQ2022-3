from dataclasses import dataclass
from typing import Optional, Dict, Any
import json
from pathlib import Path

from app.services.ai_service import get_ai_service


@dataclass
class Template:
    list_url: Optional[str] = None
    list_link_selector: Optional[str] = None
    url_prefix: Optional[str] = None

    article_title_selector: Optional[str] = None
    article_content_selector: Optional[str] = None
    article_author_selector: Optional[str] = None

    # Chuẩn hoá: dùng article_date_selector_meta
    # Giữ alias article_date_selector để tương thích ngược
    article_date_selector_meta: Optional[str] = None
    article_date_selector: Optional[str] = None  # alias


def load_template(config_json: Optional[str]) -> Template:
    if not config_json:
        return Template()
    try:
        cfg: Dict[str, Any] = json.loads(config_json)
    except Exception:
        return Template()

    article = cfg.get("article", {}) if isinstance(cfg.get("article"), dict) else {}

    # Hỗ trợ nhiều key cho selector ngày
    date_sel = (
        article.get("date_selector_meta")
        or article.get("date_selector")
        or article.get("published_time_selector")
        or article.get("date_selector_css")
    )

    return Template(
        list_url=cfg.get("list_url"),
        list_link_selector=cfg.get("list_link_selector"),
        url_prefix=cfg.get("url_prefix"),

        article_title_selector=article.get("title_selector"),
        article_content_selector=article.get("content_selector"),
        article_author_selector=article.get("author_selector"),

        article_date_selector_meta=date_sel,
        article_date_selector=date_sel,  # alias
    )


# --- Approach 2: AI-generated extraction template with caching ---

def _is_valid_config(cfg: dict | None) -> bool:
    if not isinstance(cfg, dict):
        return False
    required_top = ["list_url", "list_link_selector", "url_prefix", "article"]
    if any(k not in cfg for k in required_top):
        return False
    if not isinstance(cfg.get("article"), dict):
        return False
    required_article = ["title_selector", "content_selector", "date_selector_meta"]
    if any(k not in cfg["article"] for k in required_article):
        return False
    return True


def _config_cache_path_for(source_code: str) -> Path:
    # Store next to crawler files for clarity
    from app.crawlers import __file__ as crawlers_init
    crawlers_dir = Path(crawlers_init).parent
    return crawlers_dir / f"{source_code}_config_cache.json"


def _load_cached_config(source_code: str) -> dict | None:
    cache_path = _config_cache_path_for(source_code)
    if cache_path.exists():
        try:
            cfg = json.loads(cache_path.read_text(encoding="utf-8"))
            if _is_valid_config(cfg):
                return cfg
        except Exception:
            return None
    return None


def _save_cached_config(source_code: str, cfg: dict) -> None:
    cache_path = _config_cache_path_for(source_code)
    try:
        cache_path.write_text(json.dumps(cfg, ensure_ascii=True, indent=2), encoding="utf-8")
    except Exception:
        # Best-effort cache; ignore IO errors
        pass


def ensure_template_with_ai(source_code: str, hints: Dict[str, Any], refresh: bool = False) -> Template:
    """
    Generate an extraction template using AI once, then cache it.

    - If `refresh` is False and a valid cache exists, use the cached config.
    - Otherwise call the AI service with provided `hints` as fallback/defaults.
    - Persist the resulting config for future runs.

    Returns a `Template` instance ready for use by extractors.
    """

    if not refresh:
        cached = _load_cached_config(source_code)
        if cached:
            return load_template(json.dumps(cached))

    ai = get_ai_service()
    try:
        cfg = ai.generate_crawler_config(source_code, hints=hints)
    except Exception:
        cfg = hints

    if not _is_valid_config(cfg):
        cfg = hints

    _save_cached_config(source_code, cfg)
    return load_template(json.dumps(cfg))


def ensure_template_with_ai_from_html(
    source_code: str,
    list_html: str,
    article_html: str,
    hints: Dict[str, Any],
    refresh: bool = True,
) -> Template:
    """
    Generate an extraction template using AI, providing DOM samples
    (list and article HTML) to improve selector inference, then cache it.

    - If `refresh` is False and cache exists, returns cached config.
    - Otherwise, calls AI with `html_samples` and `hints`.
    """

    if not refresh:
        cached = _load_cached_config(source_code)
        if cached:
            return load_template(json.dumps(cached))

    ai = get_ai_service()
    try:
        cfg = ai.generate_crawler_config(
            source_code,
            hints=hints,
            html_samples={"list_html": list_html, "article_html": article_html},
        )
    except Exception:
        cfg = hints

    if not _is_valid_config(cfg):
        cfg = hints

    _save_cached_config(source_code, cfg)
    return load_template(json.dumps(cfg))