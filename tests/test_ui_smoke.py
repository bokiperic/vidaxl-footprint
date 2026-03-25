"""Playwright UI smoke tests — verify dashboard loads and renders correctly."""
import re

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="function")
def dashboard(page: Page, base_url: str) -> Page:
    page.goto(f"{base_url}/dashboard")
    # Wait for API calls to complete and content to render
    page.wait_for_load_state("networkidle")
    return page


class TestDashboardLoads:
    def test_page_title(self, dashboard: Page):
        expect(dashboard).to_have_title("Hunkemoller Digital Footprint")

    def test_header_visible(self, dashboard: Page):
        header = dashboard.get_by_test_id("header-title")
        expect(header).to_be_visible()
        expect(header).to_have_text("Hunkemoller Digital Footprint")

    def test_action_buttons_visible(self, dashboard: Page):
        expect(dashboard.get_by_test_id("btn-scrape")).to_be_visible()
        expect(dashboard.get_by_test_id("btn-scrape")).to_have_text("Scrape All Sources")
        expect(dashboard.get_by_test_id("btn-analyze")).to_be_visible()
        expect(dashboard.get_by_test_id("btn-analyze")).to_have_text("Run Analysis")


class TestKPICards:
    def test_kpi_section_visible(self, dashboard: Page):
        expect(dashboard.get_by_test_id("kpi-section")).to_be_visible()

    def test_kpi_total_reviews_populated(self, dashboard: Page):
        kpi = dashboard.get_by_test_id("kpi-total")
        expect(kpi).to_be_visible()
        # Should show a number (not the placeholder dash)
        text = kpi.text_content()
        assert text != "—", "Total reviews KPI should be populated"

    def test_kpi_active_sources_populated(self, dashboard: Page):
        kpi = dashboard.get_by_test_id("kpi-sources")
        expect(kpi).to_be_visible()
        text = kpi.text_content()
        assert text != "—", "Active sources KPI should be populated"
        assert int(text) > 0

    def test_all_four_kpi_cards(self, dashboard: Page):
        cards = dashboard.get_by_test_id(re.compile(r"^kpi-.*-card$"))
        expect(cards).to_have_count(4)


class TestCharts:
    def test_sentiment_doughnut_canvas(self, dashboard: Page):
        canvas = dashboard.get_by_test_id("chart-sentiment-doughnut")
        expect(canvas).to_be_visible()

    def test_sentiment_trend_canvas(self, dashboard: Page):
        canvas = dashboard.get_by_test_id("chart-sentiment-trend")
        expect(canvas).to_be_visible()

    def test_source_chart_canvas(self, dashboard: Page):
        canvas = dashboard.get_by_test_id("chart-source")
        expect(canvas).to_be_visible()


class TestComplaintsTable:
    def test_complaints_table_visible(self, dashboard: Page):
        table = dashboard.get_by_test_id("complaints-table")
        expect(table).to_be_visible()

    def test_complaints_table_has_headers(self, dashboard: Page):
        headers = dashboard.get_by_test_id(re.compile(r"^complaints-header-"))
        expect(headers).to_have_count(5)

    def test_complaints_table_has_rows(self, dashboard: Page):
        rows = dashboard.get_by_test_id("complaints-row")
        count = rows.count()
        assert count > 0, "Complaints table should have data rows"


class TestInsightsPanel:
    def test_insights_section_visible(self, dashboard: Page):
        section = dashboard.get_by_test_id("insights-section")
        expect(section).to_be_visible()

    def test_insights_has_content(self, dashboard: Page):
        content = dashboard.get_by_test_id("insights-content")
        expect(content).to_be_visible()
        text = content.text_content()
        assert len(text) > 20, "Insights panel should have substantial content"


class TestReviewsFeed:
    def test_reviews_feed_visible(self, dashboard: Page):
        feed = dashboard.get_by_test_id("reviews-feed")
        expect(feed).to_be_visible()

    def test_reviews_feed_has_items(self, dashboard: Page):
        items = dashboard.get_by_test_id("review-item")
        count = items.count()
        assert count > 0, "Reviews feed should have items"

    def test_review_item_structure(self, dashboard: Page):
        first = dashboard.get_by_test_id("review-item").first
        expect(first.get_by_test_id("review-author")).to_be_visible()


class TestInteractions:
    def test_scrape_button_triggers_action(self, dashboard: Page):
        dashboard.get_by_test_id("btn-scrape").click()
        # Status message should appear
        status = dashboard.get_by_test_id("status-msg")
        dashboard.wait_for_function(
            "document.querySelector('[data-testid=\"status-msg\"]').textContent.length > 0",
            timeout=5000,
        )
        text = status.text_content()
        assert "scraping" in text.lower() or "started" in text.lower() or "sources" in text.lower()

    def test_analyze_button_triggers_action(self, dashboard: Page):
        dashboard.get_by_test_id("btn-analyze").click()
        status = dashboard.get_by_test_id("status-msg")
        dashboard.wait_for_function(
            "document.querySelector('[data-testid=\"status-msg\"]').textContent.length > 0",
            timeout=5000,
        )
        text = status.text_content()
        assert "analysis" in text.lower() or "started" in text.lower()
