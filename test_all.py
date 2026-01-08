#!/usr/bin/env python3
"""
Comprehensive Playwright tests for Fotios Claude Admin Panel
Tests all major functionality
"""

from playwright.sync_api import sync_playwright, expect
import time

BASE_URL = "https://localhost:9453"

def test_all():
    with sync_playwright() as p:
        # Launch browser (ignore SSL errors for self-signed cert)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        print("\n" + "="*60)
        print("FOTIOS CLAUDE ADMIN PANEL - COMPREHENSIVE TEST")
        print("="*60)

        # ============ 1. LOGIN ============
        print("\n[1] Testing Login...")
        page.goto(f"{BASE_URL}/login")
        assert "Login" in page.title()

        page.fill('input[name="username"]', 'admin')
        page.fill('input[name="password"]', 'admin123')
        page.click('button[type="submit"]')
        page.wait_for_url("**/dashboard")
        print("    ✅ Login successful")

        # ============ 2. DASHBOARD ============
        print("\n[2] Testing Dashboard...")
        assert "Dashboard" in page.title()

        # Check stats are visible
        stats = page.locator('.stat-card').count()
        print(f"    Found {stats} stat cards")
        assert stats >= 5, "Expected at least 5 stat cards"

        # Check clickable boxes
        print("    Testing clickable stat boxes...")

        # Test Projects link
        projects_link = page.locator('a.stat-card:has-text("Projects")')
        href = projects_link.get_attribute('href')
        assert href == '/projects', f"Projects link should go to /projects, got {href}"
        print("    ✅ Projects box links correctly")

        # Test Open Tickets link
        open_link = page.locator('a.stat-card:has-text("Open Tickets")')
        href = open_link.get_attribute('href')
        assert 'status=open' in href, f"Open Tickets should filter by status=open"
        print("    ✅ Open Tickets box links correctly")

        # Test In Progress link
        progress_link = page.locator('a.stat-card:has-text("In Progress")')
        href = progress_link.get_attribute('href')
        assert 'status=in_progress' in href
        print("    ✅ In Progress box links correctly")

        # Test Pending Review link
        review_link = page.locator('a.stat-card:has-text("Pending Review")')
        href = review_link.get_attribute('href')
        assert 'status=pending_review' in href
        print("    ✅ Pending Review box links correctly")

        # ============ 3. TICKETS LIST ============
        print("\n[3] Testing Tickets List...")
        page.goto(f"{BASE_URL}/tickets")
        assert "Tickets" in page.title() or "All Tickets" in page.content()

        # Check filters exist
        filters = page.locator('.filter-btn').count()
        print(f"    Found {filters} filter buttons")
        assert filters >= 4, "Expected at least 4 filter buttons"

        # Test filter navigation
        page.click('.filter-btn:has-text("In Progress")')
        page.wait_for_url("**/tickets?status=in_progress")
        print("    ✅ Filter navigation works")

        # Go back to all
        page.click('.filter-btn:has-text("All")')
        page.wait_for_url("**/tickets")
        print("    ✅ Tickets list working")

        # ============ 4. PROJECTS LIST ============
        print("\n[4] Testing Projects List...")
        page.goto(f"{BASE_URL}/projects")

        # Check projects exist
        projects = page.locator('.card').count()
        print(f"    Found {projects} project cards")

        # Check Show Archived checkbox
        checkbox = page.locator('#showArchived')
        assert checkbox.is_visible(), "Show Archived checkbox should be visible"
        print("    ✅ Show Archived checkbox exists")

        # ============ 5. PROJECT DETAIL & ARCHIVE ============
        print("\n[5] Testing Project Detail...")
        # Click first project
        page.click('.card-actions a:first-child')
        page.wait_for_url("**/project/*")

        # Check archive button exists
        archive_btn = page.locator('button:has-text("Archive")')
        if archive_btn.count() > 0:
            print("    ✅ Archive button visible for active project")
        else:
            reopen_btn = page.locator('button:has-text("Reopen")')
            if reopen_btn.count() > 0:
                print("    ✅ Reopen button visible for archived project")

        # ============ 6. TICKET DETAIL ============
        print("\n[6] Testing Ticket Detail...")
        page.goto(f"{BASE_URL}/tickets")

        # Find a ticket and click it
        ticket_link = page.locator('.ticket-row').first
        if ticket_link.count() > 0:
            ticket_link.click()
            page.wait_for_url("**/ticket/*")

            # Check page elements
            assert page.locator('.conversation').count() > 0 or page.locator('#conversation').count() > 0
            print("    ✅ Ticket detail page loads")

            # Check for status-specific buttons
            if page.locator('button:has-text("Approve")').count() > 0:
                print("    ✅ Approve button visible for pending_review ticket")
            if page.locator('button:has-text("Request Changes")').count() > 0:
                print("    ✅ Request Changes button visible")
            if page.locator('button:has-text("Reopen")').count() > 0:
                print("    ✅ Reopen button visible for closed ticket")
        else:
            print("    ⚠️  No tickets found to test")

        # ============ 7. CONSOLE ============
        print("\n[7] Testing Console...")
        page.goto(f"{BASE_URL}/console")

        # Check ticket selector exists
        ticket_select = page.locator('#ticket-select')
        assert ticket_select.is_visible(), "Ticket selector should be visible"
        print("    ✅ Ticket selector dropdown exists")

        # Check daemon controls
        start_btn = page.locator('button:has-text("Start Daemon")')
        stop_btn = page.locator('button:has-text("Stop Daemon")')
        assert start_btn.is_visible() and stop_btn.is_visible()
        print("    ✅ Daemon controls visible")

        # Check conversation area
        conversation = page.locator('.conversation, #conversation')
        assert conversation.count() > 0
        print("    ✅ Conversation area exists")

        # ============ 8. HISTORY ============
        print("\n[8] Testing History...")
        page.goto(f"{BASE_URL}/history")
        assert "History" in page.title() or "Execution History" in page.content()

        # Check session cards
        sessions = page.locator('.session-card').count()
        print(f"    Found {sessions} session cards")

        if sessions > 0:
            # Click View Details on first session
            page.locator('.view-btn').first.click()
            page.wait_for_url("**/session/*")
            print("    ✅ Session detail page loads")

            # Check View Ticket link exists
            ticket_link = page.locator('a:has-text("View Ticket")')
            if ticket_link.count() > 0:
                print("    ✅ View Ticket link exists in session detail")
        else:
            print("    ⚠️  No sessions found")

        # ============ 9. TIMEZONE CHECK ============
        print("\n[9] Testing Timezone Display...")
        page.goto(f"{BASE_URL}/tickets")

        # Check if times are displayed (we can't verify timezone easily, but check format)
        time_elements = page.locator('.ticket-meta').all_text_contents()
        if time_elements:
            print(f"    Sample time display: {time_elements[0][:50]}...")
            print("    ✅ Times are displayed")

        # ============ 10. LOGOUT ============
        print("\n[10] Testing Logout...")
        page.click('a:has-text("Logout")')
        page.wait_for_url("**/login")
        print("    ✅ Logout successful")

        # ============ SUMMARY ============
        print("\n" + "="*60)
        print("ALL TESTS PASSED!")
        print("="*60 + "\n")

        browser.close()

if __name__ == "__main__":
    test_all()
