#!/usr/bin/env python3
"""
github_screenshot.py - Captures full-page screenshots of GitHub repo pages.

Uses Playwright headless Chromium. Output is a tall PNG (1920 x ~4000px)
representing the complete rendered repo page, used by SegmentScene for the
zoom + scroll animation.

Usage:
    from github_screenshot import capture_github_page
    path = capture_github_page("https://github.com/owner/repo", "assets/screenshots/owner_repo.png")
"""

import os
import re
import time
from pathlib import Path
from typing import Optional


SCREENSHOT_DIR = Path("assets/screenshots")
VIEWPORT_WIDTH = 1920


def _repo_id_from_url(github_url: str) -> str:
    """Convert github.com/owner/repo to owner_repo slug."""
    match = re.search(r"github\.com/([^/]+)/([^/]+)", github_url)
    if not match:
        raise ValueError(f"Not a valid GitHub URL: {github_url}")
    owner, repo = match.groups()
    return f"{owner}_{repo.rstrip('/')}".lower().replace("-", "_")


def capture_github_page(
    github_url: str,
    output_path: Optional[str] = None,
    force: bool = False,
) -> Path:
    """
    Capture a full-page screenshot of a GitHub repository page.

    Args:
        github_url:   Full GitHub URL e.g. https://github.com/owner/repo
        output_path:  Where to save the PNG. Defaults to assets/screenshots/{owner_repo}.png
        force:        Re-capture even if cached screenshot exists

    Returns:
        Path to the saved PNG file
    """
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    if output_path is None:
        slug = _repo_id_from_url(github_url)
        output_path = SCREENSHOT_DIR / f"{slug}_github.png"
    else:
        output_path = Path(output_path)

    # Return cached version if available
    if not force and output_path.exists():
        print(f"  [screenshot] Using cached: {output_path.name}")
        return output_path

    print(f"  [screenshot] Capturing {github_url} ...")

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": VIEWPORT_WIDTH, "height": 900},
            device_scale_factor=1,
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )

        page = context.new_page()

        try:
            page.goto(github_url, wait_until="networkidle", timeout=30000)
        except Exception:
            # Fallback — domcontentloaded is enough for static content
            page.goto(github_url, wait_until="domcontentloaded", timeout=20000)

        # Brief settle wait for lazy-loaded content
        time.sleep(2)

        # Clean up the page for a better screenshot:
        page.evaluate("""() => {
            // Hide sticky header so it doesn't cover content
            const header = document.querySelector('header.AppHeader');
            if (header) header.style.display = 'none';

            // Hide cookie/sign-in banners
            const banners = document.querySelectorAll(
                '.js-notice, .flash-global, [data-testid="cookie-banner"]'
            );
            banners.forEach(el => el.style.display = 'none');

            // Remove fixed/sticky elements that overlap content
            document.querySelectorAll('*').forEach(el => {
                const style = window.getComputedStyle(el);
                if (style.position === 'fixed' || style.position === 'sticky') {
                    el.style.position = 'relative';
                }
            });
        }""")

        # Take full-page screenshot
        page.screenshot(
            path=str(output_path),
            full_page=True,
            type="png",
        )

        browser.close()

    print(f"  [screenshot] Saved: {output_path.name} "
          f"({output_path.stat().st_size // 1024}KB)")
    return output_path


if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://github.com/langchain-ai/open-swe"
    path = capture_github_page(url, force=True)
    print(f"Screenshot saved to: {path}")
