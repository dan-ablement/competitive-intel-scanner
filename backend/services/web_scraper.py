"""Web scraper service using Crawl4AI for crawling competitor websites."""

from __future__ import annotations

import asyncio
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urljoin, urlparse

from sqlalchemy.orm import Session

from backend.models.feed import RSSFeed
from backend.models.feed_item import FeedItem

logger = logging.getLogger(__name__)

# Patterns that suggest a URL is an article/blog post
_ARTICLE_PATH_PATTERNS = [
    r"/blog/", r"/news/", r"/post/", r"/posts/", r"/changelog/",
    r"/article/", r"/articles/", r"/updates/", r"/announcements/",
    r"/research/", r"/insights/", r"/press/", r"/stories/",
]

# Patterns to exclude (navigation, social, etc.)
_EXCLUDE_PATTERNS = [
    r"^#", r"^mailto:", r"^tel:", r"^javascript:",
    r"twitter\.com", r"facebook\.com", r"linkedin\.com",
    r"github\.com", r"youtube\.com",
    r"/tag/", r"/tags/", r"/category/", r"/categories/", r"/author/",
    r"/login", r"/signup", r"/register", r"/privacy", r"/terms",
    r"/contact", r"/about$", r"/careers",
]


class WebScraper:
    """Crawl competitor websites and extract article content using Crawl4AI."""

    async def scrape_listing(
        self, url: str, css_selector: Optional[str] = None,
    ) -> list[dict]:
        """Crawl a listing page and extract article content.

        Returns list of dicts with keys: url, title, content, published_at
        """
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

        browser_config = BrowserConfig(headless=True)
        articles: list[dict] = []

        try:
            async with AsyncWebCrawler(config=browser_config) as crawler:
                listing_config = CrawlerRunConfig()
                if css_selector:
                    listing_config = CrawlerRunConfig(css_selector=css_selector)

                result = await crawler.arun(url=url, config=listing_config)
                if not result.success:
                    logger.error("Failed to crawl listing page %s: %s", url,
                                 getattr(result, "error_message", "unknown"))
                    return []

                article_links = self._extract_article_links(result, url, css_selector)
                logger.info("Found %d article links on %s", len(article_links), url)

                for link_url, link_title in article_links:
                    try:
                        article_result = await crawler.arun(
                            url=link_url, config=CrawlerRunConfig())
                        if not article_result.success:
                            logger.warning("Failed to crawl article %s", link_url)
                            continue
                        title = link_title or self._extract_title(article_result) or "Untitled"
                        articles.append({
                            "url": link_url,
                            "title": title[:500],
                            "content": article_result.markdown or "",
                            "published_at": datetime.now(timezone.utc),
                        })
                    except Exception as exc:
                        logger.warning("Error crawling article %s: %s", link_url, exc)
        except Exception as exc:
            logger.exception("Error during web scraping of %s: %s", url, exc)

        return articles

    def _extract_article_links(
        self, result, base_url: str, css_selector: Optional[str] = None,
    ) -> list[tuple[str, str]]:
        """Extract article links from a crawl result. Returns (url, title) tuples."""
        links: list[tuple[str, str]] = []
        seen_urls: set[str] = set()
        base_domain = urlparse(base_url).netloc
        raw_links = self._get_raw_links(result)

        for href, text in raw_links:
            if not href:
                continue
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)
            if any(re.search(pat, full_url, re.IGNORECASE) for pat in _EXCLUDE_PATTERNS):
                continue
            if parsed.netloc and parsed.netloc != base_domain:
                continue
            if full_url.rstrip("/") == base_url.rstrip("/"):
                continue
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if normalized in seen_urls:
                continue
            seen_urls.add(normalized)
            if css_selector or self._is_likely_article_url(parsed.path):
                links.append((normalized, (text or "").strip()))

        return links

    def _get_raw_links(self, result) -> list[tuple[str, str]]:
        """Extract raw (href, text) pairs from a crawl result."""
        links: list[tuple[str, str]] = []
        result_links = getattr(result, "links", None)
        if result_links:
            if isinstance(result_links, dict):
                for link_list in result_links.values():
                    if isinstance(link_list, list):
                        for link in link_list:
                            if isinstance(link, dict):
                                links.append((link.get("href", ""), link.get("text", "")))
                            elif isinstance(link, str):
                                links.append((link, ""))
            elif isinstance(result_links, list):
                for link in result_links:
                    if isinstance(link, dict):
                        links.append((link.get("href", ""), link.get("text", "")))
                    elif isinstance(link, str):
                        links.append((link, ""))
        if not links:
            html = getattr(result, "html", None)
            if html:
                links = self._parse_links_from_html(html)
        return links

    def _parse_links_from_html(self, html: str) -> list[tuple[str, str]]:
        """Parse <a> tags from raw HTML as a fallback."""
        links: list[tuple[str, str]] = []
        pattern = r'<a\s[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>'
        for match in re.finditer(pattern, html, re.IGNORECASE | re.DOTALL):
            href = match.group(1)
            text = re.sub(r"<[^>]+>", "", match.group(2)).strip()
            links.append((href, text))
        return links

    def _is_likely_article_url(self, path: str) -> bool:
        """Check if a URL path looks like an article/blog post."""
        if not path or path == "/":
            return False
        for pattern in _ARTICLE_PATH_PATTERNS:
            if re.search(pattern, path, re.IGNORECASE):
                parts = [p for p in path.split("/") if p]
                if len(parts) >= 2:
                    return True
        return False

    def _extract_title(self, result) -> Optional[str]:
        """Try to extract a page title from a crawl result."""
        metadata = getattr(result, "metadata", None)
        if metadata and isinstance(metadata, dict):
            title = metadata.get("title")
            if title:
                return title.strip()
        html = getattr(result, "html", None)
        if html:
            match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        return None

    def process_feed(self, feed: RSSFeed, db: Session) -> int:
        """Synchronous entry point for FeedChecker integration.

        Runs the async scraping from a sync context, creates FeedItem records.
        Returns count of new items.
        """
        now = datetime.now(timezone.utc)
        feed.last_checked_at = now

        # Run async scraping from sync context
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    articles = pool.submit(
                        asyncio.run,
                        self.scrape_listing(feed.url, feed.css_selector),
                    ).result()
            else:
                articles = loop.run_until_complete(
                    self.scrape_listing(feed.url, feed.css_selector)
                )
        except RuntimeError:
            articles = asyncio.run(
                self.scrape_listing(feed.url, feed.css_selector)
            )

        if not articles:
            logger.info("No articles found for web scrape feed '%s' (%s)", feed.name, feed.url)
            feed.last_successful_at = now
            feed.error_count = 0
            feed.last_error = None
            db.commit()
            return 0

        new_count = 0
        for article in articles:
            article_url = article["url"]
            existing = (
                db.query(FeedItem.id)
                .filter(FeedItem.feed_id == feed.id, FeedItem.guid == article_url)
                .first()
            )
            if existing:
                continue
            item = FeedItem(
                id=uuid.uuid4(),
                feed_id=feed.id,
                guid=article_url,
                title=article.get("title", "Untitled")[:500],
                url=article_url[:2000],
                author=None,
                published_at=article.get("published_at", now),
                raw_content=article.get("content", ""),
                is_processed=False,
            )
            db.add(item)
            new_count += 1

        feed.last_successful_at = now
        feed.error_count = 0
        feed.last_error = None
        db.commit()

        logger.info("Web scrape feed '%s': found %d articles, %d new",
                     feed.name, len(articles), new_count)
        return new_count

