"""
Discover Tunisian Instagram usernames via hashtag pages.
Uses Playwright + stealth (same approach as TikTok scraper) to log in
and extract usernames from recent posts on hashtag pages.
Falls back to an empty list if credentials are missing or login fails.
"""
import asyncio
import logging
import random
import re
from typing import List, Optional

logger = logging.getLogger(__name__)

TUNISIAN_HASHTAGS = [
    "tunisie",
    "tunisia",
    "madeintunisia",
    "tunisian",
    "influenceur_tunisien",
    "tunisienne",
    "tunisialife",
    "sousse",
    "sfax",
    "nabeul",
    "hammamet",
    "bizerte",
]


async def _extract_usernames_from_page(page) -> List[str]:
    """Extract usernames from an Instagram hashtag page's JSON blob."""
    try:
        content = await page.content()
        # Look for username patterns inside the page's JSON data
        # Instagram embeds profile data in script tags
        matches = re.findall(r'"username"\s*:\s*"([a-zA-Z0-9_.]+)"', content)
        return list(set(m.lower() for m in matches if m))
    except Exception:
        return []


async def discover_tunisian_usernames(
    extra_hashtags: Optional[List[str]] = None,
    delay_range: tuple = (4.0, 8.0),
) -> List[str]:
    """
    Use Playwright to log in to Instagram and visit hashtag pages,
    collecting usernames from post data embedded in the page HTML.
    Returns a de-duplicated list. Returns [] if credentials are missing.
    """
    from ..config import settings

    ig_username = settings.ig_username
    ig_password = settings.ig_password

    if not ig_username or not ig_password:
        logger.warning("No IG credentials set — discovery skipped.")
        return []

    hashtags = list(TUNISIAN_HASHTAGS)
    if extra_hashtags:
        hashtags.extend(extra_hashtags)

    seen: set = set()
    results: List[str] = []

    try:
        from playwright.async_api import async_playwright
        from playwright_stealth import Stealth
    except ImportError as e:
        logger.error("Playwright/stealth not available: %s", e)
        return []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=["--headless=new"])
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
            ),
            viewport={"width": 390, "height": 844},
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        # Step 1: Log in
        try:
            await page.goto("https://www.instagram.com/accounts/login/", wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)
            await page.fill('input[name="username"]', ig_username)
            await page.fill('input[name="password"]', ig_password)
            await page.click('button[type="submit"]')
            await page.wait_for_url(re.compile(r"instagram\.com(?!/accounts/login)"), timeout=20000)
            await asyncio.sleep(3)
            # Dismiss any post-login dialogs
            for selector in ['button:has-text("Not Now")', 'button:has-text("Cancel")']:
                try:
                    btn = page.locator(selector).first
                    if await btn.is_visible(timeout=3000):
                        await btn.click()
                        await asyncio.sleep(1)
                except Exception:
                    pass
            logger.info("Instagram login successful")
        except Exception as e:
            logger.warning("Instagram login failed: %s", e)
            await browser.close()
            return []

        # Step 2: Visit each hashtag page
        for hashtag in hashtags:
            try:
                url = f"https://www.instagram.com/explore/tags/{hashtag}/"
                await page.goto(url, wait_until="networkidle", timeout=25000)
                await asyncio.sleep(random.uniform(*delay_range))

                usernames = await _extract_usernames_from_page(page)
                new_count = 0
                for u in usernames:
                    # Filter out obvious non-user values (IG internal names, etc.)
                    if len(u) < 3 or u in ("instagram", "explore", "reels"):
                        continue
                    if u not in seen:
                        seen.add(u)
                        results.append(u)
                        new_count += 1
                logger.info("Hashtag #%s: found %d new usernames", hashtag, new_count)
            except Exception as e:
                logger.warning("Error fetching hashtag #%s: %s", hashtag, e)

        await browser.close()

    logger.info("Discovery complete: %d unique usernames from %d hashtags", len(results), len(hashtags))
    return results
