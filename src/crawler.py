
import argparse
import asyncio
from collections import deque
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from playwright.async_api import async_playwright


USER_AGENT = "AgriResearchBot/1.0"
MAX_PAGES = 20


async def crawl(start_url: str):
    start = urlparse(start_url)

    if start.scheme != "https" or not start.hostname:
        raise ValueError("Use a valid HTTPS website URL.")

    # Keep crawling within the starting hostname.
    hostname = start.hostname
    robots_url = f"{start.scheme}://{start.netloc}/robots.txt"

    async with httpx.AsyncClient(
        timeout=30,
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
    ) as client:
        robots_response = await client.get(robots_url)
        robots_response.raise_for_status()

        robots = RobotFileParser()
        robots.parse(robots_response.text.splitlines())

        def allowed(url):
            parts = urlparse(url)
            return (
                parts.scheme == "https"
                and parts.hostname == hostname
                and robots.can_fetch(USER_AGENT, url)
            )

        queue = deque([start_url])
        visited = set()
        pdf_urls = set()

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=True
            )

            page = await browser.new_page(
                user_agent=USER_AGENT,
                accept_downloads=False,
            )

            try:
                while queue and len(visited) < MAX_PAGES:
                    url = queue.popleft()

                    if url in visited or not allowed(url):
                        continue

                    visited.add(url)

                    try:
                        response = await page.goto(
                            url,
                            wait_until="domcontentloaded",
                            timeout=30000,
                        )

                        if response is None or response.status >= 400:
                            continue

                        if not allowed(page.url):
                            continue

                        links = await page.locator(
                            "a[href]"
                        ).evaluate_all(
                            """elements => elements.map(
                                a => a.href
                            )"""
                        )

                        for href in links:
                            link = urljoin(page.url, href)
                            parsed = urlparse(link)

                            if not allowed(link):
                                continue

                            if parsed.path.lower().endswith(".pdf"):
                                pdf_urls.add(link)

                            elif (
                                link not in visited
                                and link not in queue
                                and not parsed.path.lower().endswith(
                                    (".jpg", ".png", ".zip", ".mp4")
                                )
                            ):
                                queue.append(link)

                        print(
                            f"Visited {len(visited)} pages; "
                            f"PDF links: {len(pdf_urls)}"
                        )

                        await asyncio.sleep(1.5)

                    except Exception as exc:
                        print("Page error:", url, exc)

            finally:
                await browser.close()

    return sorted(pdf_urls)


async def run(url):
    links = await crawl(url)

    with open(
        "data/processed/pdf_urls.txt",
        "w",
        encoding="utf-8",
    ) as file:
        file.write("\n".join(links))

    print("Total discovered PDF URLs:", len(links))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    args = parser.parse_args()

    asyncio.run(run(args.url))
