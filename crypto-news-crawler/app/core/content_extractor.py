import json
from typing import List, Optional, Tuple
from urllib.parse import urljoin

import dateparser
import trafilatura
from bs4 import BeautifulSoup

from .structure_learner import Template

DATE_META_SELECTORS = [
    "meta[property='article:published_time']",
    "meta[property='article:modified_time']",
    "meta[property='og:updated_time']",
    "meta[itemprop='datePublished']",
    "meta[itemprop='dateModified']",
    "meta[name='pubdate']",
]

def is_feed(text: str) -> bool:
    t = (text or "").lstrip().lower()
    return t.startswith("<?xml") or "<rss" in t or "<feed" in t

def extract_feed_links_and_dates(list_xml: str) -> List[Tuple[str, Optional[str]]]:
    """
    Parse RSS/Atom và trả về [(url, pubDateStr|updatedStr|None), ...]
    """
    soup = BeautifulSoup(list_xml, "xml")
    items: List[Tuple[str, Optional[str]]] = []

    # RSS
    for item in soup.find_all("item"):
        link_tag = item.find("link")
        link = link_tag.get_text(strip=True) if link_tag else None
        # pubDate; một số feed dùng dc:date
        pub_tag = item.find("pubDate") or item.find("dc:date")
        pub_date = pub_tag.get_text(strip=True) if pub_tag else None
        if link:
            items.append((link, pub_date if pub_date else None))

    # Atom
    for entry in soup.find_all("entry"):
        # link rel="alternate" ưu tiên; nếu không có, lấy link đầu tiên có href
        link_el = entry.find("link", attrs={"rel": ["alternate", None]}) or entry.find("link", href=True)
        href = link_el.get("href") if link_el and link_el.has_attr("href") else None
        updated_el = entry.find("updated") or entry.find("published")
        updated = updated_el.get_text(strip=True) if updated_el else None
        if href:
            items.append((href, updated if updated else None))

    # loại trùng theo url, giữ date đầu tiên
    seen = {}
    for url, d in items:
        if url and url not in seen:
            seen[url] = d
    return [(u, seen[u]) for u in seen.keys()]

def extract_links(list_html: str, template: Template, base_url: Optional[str]) -> List[str]:
    """
    Trả về danh sách URL bài viết từ list HTML.
    """
    soup = BeautifulSoup(list_html, "lxml")
    urls = set()

    anchors = soup.select(template.list_link_selector) if template.list_link_selector else soup.find_all("a", href=True)
    prefix = template.url_prefix or (base_url.rstrip("/") if base_url else "")

    for a in anchors:
        href = a.get("href")
        if not href:
            continue
        if href.startswith("http"):
            full_url = href
        else:
            full_url = urljoin(prefix + "/", href)
        if full_url.startswith(("mailto:", "tel:", "javascript:")):
            continue
        urls.add(full_url)

    return list(urls)

def _try_parse_date_from_meta(soup: BeautifulSoup, custom_selector: Optional[str]) -> Optional[str]:
    # normalize “article:published_time” -> meta[property='article:published_time']
    selectors = []
    if custom_selector:
        if ":" in custom_selector and "[" not in custom_selector:
            custom_selector = f"meta[property='{custom_selector}']"
        selectors.append(custom_selector)
    selectors.extend(DATE_META_SELECTORS)

    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            val = el.get("content") or el.get("datetime")
            if val:
                return val
    return None

def extract_article_from_html(article_html: str, template: Template) -> Optional[dict]:
    soup = BeautifulSoup(article_html, "lxml")

    title = None
    content = None
    published_at = None
    author = None

    if template.article_title_selector:
        el = soup.select_one(template.article_title_selector)
        if el:
            title = el.get_text(strip=True)

    if template.article_content_selector:
        el = soup.select_one(template.article_content_selector)
        if el:
            content = el.get_text("\n", strip=True)

    # author via selector
    if getattr(template, "article_author_selector", None):
        el = soup.select_one(template.article_author_selector)
        if el:
            author = el.get_text(strip=True)

    # author via meta fallbacks
    if not author:
        for sel in [
            "meta[name='author']",
            "meta[property='article:author']",
            "meta[name='byl']",
            "[itemprop='author']",
            "a[rel='author']",
            ".byline, .byline__name, .article__byline, .author, .author-name",
        ]:
            el = soup.select_one(sel)
            if el:
                val = el.get("content") if el.name == "meta" else el.get_text(strip=True)
                if val:
                    author = val
                    break

    # date via meta selectors
    date_selector = getattr(template, "article_date_selector_meta", None) or getattr(template, "article_date_selector", None)
    date_str = _try_parse_date_from_meta(soup, date_selector)
    if date_str:
        try:
            published_at = dateparser.parse(date_str)
        except Exception:
            published_at = None

    # fallback time tag
    if not published_at:
        time_el = soup.find("time")
        if time_el:
            val = time_el.get("datetime") or time_el.get_text(strip=True)
            if val:
                try:
                    published_at = dateparser.parse(val)
                except Exception:
                    published_at = None

    # fallback trafilatura
    if not title or not content or not published_at:
        try:
            extracted = trafilatura.extract(
                article_html,
                include_comments=False,
                include_tables=False,
                output_format="json",
                with_metadata=True
            )
            if extracted:
                data = json.loads(extracted)
                title = title or data.get("title")
                content = content or data.get("text")
                if not published_at and data.get("date"):
                    try:
                        published_at = dateparser.parse(data["date"])
                    except Exception:
                        published_at = None
        except Exception:
            pass

    if not content:
        return None

    return {
        "title": title,
        "content": content,
        "published_at": published_at,
        "author": author,
    }