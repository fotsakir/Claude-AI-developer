#!/usr/bin/env python3
"""
@file: verify_ui.py
@description: Complete UI verification - screenshots, console errors, links
@usage: python verify_ui.py <url> [output_path]
@tags: #testing #ui #playwright
"""

import sys
import os
from urllib.parse import urljoin

def verify_page(url, output_path="/tmp"):
    """
    Complete page verification:
    - Desktop + Mobile screenshots
    - Console errors capture
    - Failed requests capture
    - All links extraction
    """
    from playwright.sync_api import sync_playwright

    results = {
        "url": url,
        "console_errors": [],
        "console_warnings": [],
        "failed_requests": [],
        "all_links": [],
        "screenshots": {}
    }

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        # Capture console messages
        def handle_console(msg):
            if msg.type == "error":
                results["console_errors"].append(msg.text)
            elif msg.type == "warning":
                results["console_warnings"].append(msg.text)

        page.on("console", handle_console)

        # Capture failed requests (404, CORS, etc.)
        page.on("requestfailed", lambda req:
            results["failed_requests"].append(f"{req.url} - {req.failure}")
        )

        # Navigate to page
        page.goto(url)
        page.wait_for_load_state("networkidle")

        # Desktop screenshot
        page.set_viewport_size({"width": 1920, "height": 1080})
        desktop_path = f"{output_path}/screenshot_desktop.png"
        page.screenshot(path=desktop_path, full_page=True)
        results["screenshots"]["desktop"] = desktop_path

        # Mobile screenshot
        page.set_viewport_size({"width": 375, "height": 667})
        mobile_path = f"{output_path}/screenshot_mobile.png"
        page.screenshot(path=mobile_path, full_page=True)
        results["screenshots"]["mobile"] = mobile_path

        # Extract all links
        for a in page.query_selector_all("a[href]"):
            href = a.get_attribute("href")
            if href and not href.startswith("#") and not href.startswith("javascript:"):
                results["all_links"].append(urljoin(url, href))

        # Extract all images
        for img in page.query_selector_all("img[src]"):
            results["all_links"].append(urljoin(url, img.get_attribute("src")))

        browser.close()

    return results

def print_results(results):
    """Print verification results in readable format."""
    print("=" * 50)
    print(f"URL: {results['url']}")
    print("=" * 50)

    print("\n=== SCREENSHOTS ===")
    print(f"Desktop: {results['screenshots']['desktop']}")
    print(f"Mobile:  {results['screenshots']['mobile']}")

    print("\n=== CONSOLE ERRORS ===")
    if results["console_errors"]:
        for e in results["console_errors"]:
            print(f"  {e}")
    else:
        print("  None")

    print("\n=== CONSOLE WARNINGS ===")
    if results["console_warnings"]:
        for w in results["console_warnings"]:
            print(f"  {w}")
    else:
        print("  None")

    print("\n=== FAILED REQUESTS ===")
    if results["failed_requests"]:
        for f in results["failed_requests"]:
            print(f"  {f}")
    else:
        print("  None")

    print(f"\n=== LINKS FOUND: {len(results['all_links'])} ===")
    for link in results["all_links"][:20]:
        print(f"  {link}")
    if len(results["all_links"]) > 20:
        print(f"  ... and {len(results['all_links']) - 20} more")

    # Summary
    print("\n" + "=" * 50)
    errors = len(results["console_errors"]) + len(results["failed_requests"])
    if errors == 0:
        print("RESULT: All checks passed")
    else:
        print(f"RESULT: {errors} issue(s) found - fix before completing task!")
    print("=" * 50)

    return errors == 0

def test_links(links, verify_ssl=False):
    """Test all links for 404s."""
    import requests

    print("\n=== TESTING LINKS ===")
    broken = []
    for url in set(links):
        if url and not url.startswith('#'):
            try:
                r = requests.head(url, timeout=10, verify=verify_ssl, allow_redirects=True)
                status = "OK" if r.status_code < 400 else "BROKEN"
                if r.status_code >= 400:
                    broken.append((url, r.status_code))
                    print(f"  {r.status_code} {url}")
            except Exception as e:
                broken.append((url, str(e)))
                print(f"  ERROR {url}: {e}")

    if not broken:
        print("  All links OK!")
    return broken

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_ui.py <url> [output_path]")
        print("Example: python verify_ui.py https://127.0.0.1:9867/myproject/")
        sys.exit(1)

    url = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "/tmp"

    # Ensure output path exists
    os.makedirs(output_path, exist_ok=True)

    # Run verification
    results = verify_page(url, output_path)
    success = print_results(results)

    # Optionally test all links
    if "--test-links" in sys.argv:
        test_links(results["all_links"])

    sys.exit(0 if success else 1)
