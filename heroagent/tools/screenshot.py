"""
HeroAgent Screenshot Tool

Take screenshots using Playwright with full page verification:
- Desktop + Mobile screenshots
- Console errors capture
- Failed requests capture
- All links extraction
"""

import os
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin

from .base import BaseTool, ToolResult

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False


class ScreenshotTool(BaseTool):
    """Take screenshots and verify web pages (console errors, failed requests, links)."""

    name = "Screenshot"
    description = """Take screenshots of a web page with FULL verification:
- Desktop + Mobile screenshots (full_page=True)
- Console errors capture (must be ZERO!)
- Failed requests capture (404s, CORS errors)
- All links extraction for verification
Returns screenshots paths AND any errors found."""

    VIEWPORTS = {
        'desktop': {'width': 1920, 'height': 1080},
        'mobile': {'width': 375, 'height': 667},
        'tablet': {'width': 768, 'height': 1024},
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.timeout = self.config.get('timeout', 30000)
        self.wait_time = self.config.get('wait_time', 2000)

    def execute(
        self,
        url: str,
        output: Optional[str] = None,
        viewport: str = "both",
        full_page: bool = True,
        **kwargs
    ) -> ToolResult:
        """Take screenshot(s) of a web page with full verification.

        Args:
            url: URL to screenshot
            output: Output path (without extension for 'both' mode)
            viewport: 'desktop', 'mobile', 'tablet', or 'both' (desktop+mobile)
            full_page: Capture full page (default True per global context rules)

        Returns:
            ToolResult with screenshot path(s), console errors, failed requests, and links
        """
        if not HAS_PLAYWRIGHT:
            return ToolResult(
                output="Error: Playwright not installed. Run: pip install playwright && playwright install chromium",
                is_error=True
            )

        if not url:
            return ToolResult(output="Error: No URL provided", is_error=True)

        # Default output path
        if not output:
            output = "/tmp/screenshot"

        # Ensure output directory exists
        output_dir = os.path.dirname(output) if os.path.dirname(output) else "."
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Remove extension if provided (we'll add it)
        if output.endswith('.png'):
            output = output[:-4]

        screenshots_taken = []
        console_errors: List[str] = []
        console_warnings: List[str] = []
        failed_requests: List[str] = []
        all_links: List[str] = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                context = browser.new_context(ignore_https_errors=True)
                page = context.new_page()

                # Capture console messages
                def handle_console(msg):
                    if msg.type == "error":
                        console_errors.append(msg.text)
                    elif msg.type == "warning":
                        console_warnings.append(msg.text)
                page.on("console", handle_console)

                # Capture failed requests (404, CORS, etc.)
                def handle_request_failed(req):
                    failed_requests.append(f"{req.url} - {req.failure}")
                page.on("requestfailed", handle_request_failed)

                # Navigate
                page.goto(url, timeout=self.timeout)
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(self.wait_time)  # Wait for animations

                # Extract all links
                for a in page.query_selector_all("a[href]"):
                    href = a.get_attribute("href")
                    if href and not href.startswith("#") and not href.startswith("javascript:"):
                        all_links.append(urljoin(url, href))

                # Extract all images (to check for broken images)
                for img in page.query_selector_all("img[src]"):
                    src = img.get_attribute("src")
                    if src:
                        all_links.append(urljoin(url, src))

                # Determine viewports to capture
                if viewport == "both":
                    viewports_to_capture = ['desktop', 'mobile']
                else:
                    viewports_to_capture = [viewport]

                for vp_name in viewports_to_capture:
                    vp = self.VIEWPORTS.get(vp_name, self.VIEWPORTS['desktop'])
                    page.set_viewport_size(vp)

                    # Build output filename
                    if len(viewports_to_capture) > 1:
                        out_path = f"{output}_{vp_name}.png"
                    else:
                        out_path = f"{output}.png"

                    page.screenshot(path=out_path, full_page=full_page)
                    screenshots_taken.append(out_path)

                browser.close()

            # Build result output
            result_lines = []

            # Screenshots
            result_lines.append("=== SCREENSHOTS ===")
            for path in screenshots_taken:
                result_lines.append(f"✅ {path}")

            # Console errors (CRITICAL!)
            result_lines.append("\n=== CONSOLE ERRORS ===")
            if console_errors:
                for err in console_errors:
                    result_lines.append(f"❌ {err}")
                result_lines.append(f"\n⚠️ FOUND {len(console_errors)} CONSOLE ERRORS - MUST FIX!")
            else:
                result_lines.append("✅ No console errors")

            # Failed requests (CRITICAL!)
            result_lines.append("\n=== FAILED REQUESTS ===")
            if failed_requests:
                for req in failed_requests:
                    result_lines.append(f"❌ {req}")
                result_lines.append(f"\n⚠️ FOUND {len(failed_requests)} FAILED REQUESTS - MUST FIX!")
            else:
                result_lines.append("✅ All requests OK")

            # Warnings (informational)
            if console_warnings:
                result_lines.append(f"\n=== WARNINGS ({len(console_warnings)}) ===")
                for warn in console_warnings[:5]:  # Limit to first 5
                    result_lines.append(f"⚠️ {warn}")
                if len(console_warnings) > 5:
                    result_lines.append(f"... and {len(console_warnings) - 5} more")

            # Links found
            unique_links = list(set(all_links))
            result_lines.append(f"\n=== LINKS FOUND: {len(unique_links)} ===")

            # Determine if there are critical issues
            has_errors = len(console_errors) > 0 or len(failed_requests) > 0

            return ToolResult(
                output="\n".join(result_lines),
                metadata={
                    'paths': screenshots_taken,
                    'console_errors': console_errors,
                    'console_warnings': console_warnings,
                    'failed_requests': failed_requests,
                    'links': unique_links,
                    'has_errors': has_errors
                }
            )

        except Exception as e:
            return ToolResult(output=f"Error taking screenshot: {str(e)}", is_error=True)

    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema."""
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to screenshot"
                },
                "output": {
                    "type": "string",
                    "description": "Output path (without extension). Default: /tmp/screenshot"
                },
                "viewport": {
                    "type": "string",
                    "enum": ["desktop", "mobile", "tablet", "both"],
                    "description": "Viewport size. 'both' captures desktop and mobile. Default: both"
                },
                "full_page": {
                    "type": "boolean",
                    "description": "Capture full page scroll. Default: true"
                }
            },
            "required": ["url"]
        }
