import os
import httpx
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def fetch_html(url: str, timeout: float = 20.0) -> str:
    resp = httpx.get(url, headers=DEFAULT_HEADERS, timeout=timeout, follow_redirects=True)
    resp.raise_for_status()
    return resp.text


def fetch_html_rendered(url: str, timeout: float = 30.0) -> str:
    """
    Fetch fully rendered HTML using Playwright if available, otherwise fallback to requests.

    - Uses Chromium headless and waits for network idle.
    - Applies DEFAULT_HEADERS via extra HTTP headers.
    - If Playwright times out or fails, falls back to plain HTTP fetch.
    """
    # Allow disabling rendered fetch via env flag
    if os.getenv("ENABLE_RENDERED_FETCH") != "1":
        return fetch_html(url, timeout=timeout)

    if sync_playwright is None:
        # Fallback to plain HTTP fetch
        return fetch_html(url, timeout=timeout)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                context = browser.new_context(
                    user_agent=DEFAULT_HEADERS.get("User-Agent"),
                    extra_http_headers={
                        k: v
                        for k, v in DEFAULT_HEADERS.items()
                        if k not in {"User-Agent"}
                    },
                    bypass_csp=True,
                )
                page = context.new_page()
                page.set_default_timeout(int(timeout * 1000))
                page.goto(url, wait_until="networkidle")
                html = page.content()
                return html
            finally:
                try:
                    browser.close()
                except Exception:
                    pass
    except Exception as e:
        # Timeout or other Playwright error - fallback to plain fetch
        print(f"[Fetcher] Playwright failed ({type(e).__name__}), falling back to plain fetch: {url}")
        return fetch_html(url, timeout=timeout)
