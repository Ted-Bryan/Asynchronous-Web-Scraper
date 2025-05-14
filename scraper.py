"""
Sophisticated asynchronous web scraper.

Features
--------
* Fully async networking (aiohttp, asyncio)
* Pluggable parser functions
* robots.txt compliance
* Exponential back-off + retry
* Concurrency & delay controls
* CSV export helper
"""

from __future__ import annotations
import asyncio, csv, logging
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Any, Optional
from urllib.parse import urlparse
from urllib import robotparser

import aiohttp, async_timeout
from bs4 import BeautifulSoup


# ────────────────────────────────
# Configuration
# ────────────────────────────────
@dataclass
class ScraperConfig:
    concurrency: int = 10          # simultaneous requests
    delay: float = 0.5             # polite pause (s) between requests
    request_timeout: int = 15      # per-request hard timeout
    max_retries: int = 3
    backoff_factor: float = 0.5    # 0.5, 1.0, 2.0 … between retries
    user_agent: str = (
        "Mozilla/5.0 (compatible; SophisticatedScraper/1.0; +https://example.com/bot)"
    )
    headers: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        self.headers.setdefault("User-Agent", self.user_agent)


# ────────────────────────────────
# Main asynchronous spider
# ────────────────────────────────
class AsyncScraper:
    """Core scraper class."""

    def __init__(self, config: ScraperConfig, parser: Callable[[str, str], Dict[str, Any]]):
        self.config = config
        self.parser = parser
        self.semaphore = asyncio.Semaphore(config.concurrency)
        self.results: List[Dict[str, Any]] = []

        # Internals
        self._logger = self._setup_logger()
        self._robot_cache: Dict[str, robotparser.RobotFileParser] = {}
        self._session: Optional[aiohttp.ClientSession] = None

    # ----------------------------
    # Public helpers
    # ----------------------------
    async def scrape(self, urls: List[str]) -> None:
        """Crawl a list of URLs and fill `self.results`."""
        async with aiohttp.ClientSession() as self._session:
            tasks = [self._scrape_one(u) for u in urls]
            await asyncio.gather(*tasks)

    def export_csv(self, path: str) -> None:
        """Write the collected data to CSV."""
        if not self.results:
            self._logger.warning("No results to export.")
            return

        keys = sorted(self.results[0].keys())
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=keys)
            writer.writeheader()
            writer.writerows(self.results)
        self._logger.info("Exported %d rows → %s", len(self.results), path)

    # ----------------------------
    # Internal machinery
    # ----------------------------
    async def _scrape_one(self, url: str) -> None:
        html = await self._fetch(url)
        if not html:
            return

        try:
            data = self.parser(url, html)
            self.results.append(data)
            self._logger.info("Parsed %s", url)
        except Exception as exc:
            self._logger.exception("Parser failed for %s: %s", url, exc)

    async def _fetch(self, url: str) -> Optional[str]:
        if not await self._allowed_by_robots(url):
            self._logger.warning("Disallowed by robots.txt: %s", url)
            return None

        for attempt in range(self.config.max_retries):
            try:
                async with self.semaphore:
                    await asyncio.sleep(self.config.delay)
                    async with async_timeout.timeout(self.config.request_timeout):
                        async with self._session.get(url, headers=self.config.headers) as r:
                            r.raise_for_status()
                            return await r.text()
            except Exception as exc:
                wait = self.config.backoff_factor * (2 ** attempt)
                self._logger.warning("Attempt %d for %s failed (%s). Sleeping %.1fs",
                                     attempt + 1, url, exc, wait)
                await asyncio.sleep(wait)
        self._logger.error("Gave up on %s after %d retries", url, self.config.max_retries)
        return None

    async def _allowed_by_robots(self, url: str) -> bool:
        """Cache + consult robots.txt."""
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if base not in self._robot_cache:
            rp = robotparser.RobotFileParser()
            try:
                async with self._session.get(f"{base}/robots.txt", headers=self.config.headers) as r:
                    rp.parse((await r.text()).splitlines())
            except Exception:
                # Could not fetch: default to allow
                self._logger.debug("No robots.txt at %s", base)
            self._robot_cache[base] = rp
        return self._robot_cache[base].can_fetch(self.config.user_agent, url)

    @staticmethod
    def _setup_logger() -> logging.Logger:
        logger = logging.getLogger("AsyncScraper")
        if not logger.handlers:
            h = logging.StreamHandler()
            h.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
            logger.addHandler(h)
        logger.setLevel(logging.INFO)
        return logger


# ────────────────────────────────
# Example parser (title + meta-description)
# ────────────────────────────────
def default_parser(url: str, html: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    title = soup.title.string.strip() if soup.title else ""
    meta = soup.find("meta", attrs={"name": "description"})
    desc = meta["content"].strip() if meta and "content" in meta.attrs else ""
    return {"url": url, "title": title, "description": desc}


# ────────────────────────────────
# CLI entry point
# ────────────────────────────────
async def _cli() -> None:
    import argparse, pathlib

    p = argparse.ArgumentParser(description="Sophisticated async web scraper")
    p.add_argument("urlfile", help="Path to text file with one URL per line")
    p.add_argument("-o", "--output", default="output.csv", help="CSV destination")
    p.add_argument("-c", "--concurrency", type=int, default=10, help="Parallel requests")
    args = p.parse_args()

    conf = ScraperConfig(concurrency=args.concurrency)
    spider = AsyncScraper(conf, default_parser)

    urls = pathlib.Path(args.urlfile).read_text().splitlines()
    urls = [u.strip() for u in urls if u.strip()]

    await spider.scrape(urls)
    spider.export_csv(args.output)


if __name__ == "__main__":          # pragma: no cover
    try:
        asyncio.run(_cli())
    except KeyboardInterrupt:
        pass