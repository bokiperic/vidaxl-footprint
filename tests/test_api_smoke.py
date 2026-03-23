"""Playwright API smoke tests — verify backend endpoints respond correctly."""
import pytest
from playwright.sync_api import APIRequestContext, Playwright


@pytest.fixture(scope="session")
def api_context(playwright: Playwright, base_url: str) -> APIRequestContext:
    ctx = playwright.request.new_context(base_url=base_url)
    yield ctx
    ctx.dispose()


class TestRootAndHealth:
    def test_root_returns_app_info(self, api_context: APIRequestContext):
        resp = api_context.get("/")
        assert resp.ok
        body = resp.json()
        assert body["app"] == "VidaXL Digital Footprint"
        assert "version" in body
        assert "mock_mode" in body

    def test_docs_available(self, api_context: APIRequestContext):
        resp = api_context.get("/docs")
        assert resp.ok
        assert "swagger" in resp.text().lower() or "openapi" in resp.text().lower()


class TestReviewsAPI:
    def test_list_reviews(self, api_context: APIRequestContext):
        resp = api_context.get("/api/v1/reviews?page=1&page_size=5")
        assert resp.ok
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert "page" in body
        assert body["page"] == 1

    def test_list_reviews_with_filters(self, api_context: APIRequestContext):
        resp = api_context.get("/api/v1/reviews?sentiment=POS&page_size=3")
        assert resp.ok
        body = resp.json()
        for item in body["items"]:
            assert item["sentiment"] == "POS"

    def test_review_stats(self, api_context: APIRequestContext):
        resp = api_context.get("/api/v1/reviews/stats")
        assert resp.ok
        body = resp.json()
        assert "total_reviews" in body
        assert "avg_rating" in body
        assert "sentiment_counts" in body
        assert isinstance(body["total_reviews"], int)


class TestArticlesAPI:
    def test_list_articles(self, api_context: APIRequestContext):
        resp = api_context.get("/api/v1/articles?page=1&page_size=5")
        assert resp.ok
        body = resp.json()
        assert "items" in body
        assert "total" in body


class TestDashboardAPI:
    def test_overview(self, api_context: APIRequestContext):
        resp = api_context.get("/api/v1/dashboard/overview")
        assert resp.ok
        body = resp.json()
        assert "total_reviews" in body
        assert "avg_rating" in body
        assert "avg_sentiment_score" in body
        assert "active_sources" in body
        assert body["active_sources"] > 0

    def test_complaints(self, api_context: APIRequestContext):
        resp = api_context.get("/api/v1/dashboard/complaints")
        assert resp.ok
        body = resp.json()
        assert "complaints" in body
        if body["complaints"]:
            c = body["complaints"][0]
            assert "theme" in c
            assert "frequency" in c
            assert "severity" in c

    def test_products(self, api_context: APIRequestContext):
        resp = api_context.get("/api/v1/dashboard/products")
        assert resp.ok
        body = resp.json()
        assert "best" in body
        assert "worst" in body

    def test_trends(self, api_context: APIRequestContext):
        resp = api_context.get("/api/v1/dashboard/trends")
        assert resp.ok
        body = resp.json()
        assert "monthly" in body

    def test_sources(self, api_context: APIRequestContext):
        resp = api_context.get("/api/v1/dashboard/sources")
        assert resp.ok
        body = resp.json()
        assert "sources" in body
        assert len(body["sources"]) > 0

    def test_insights(self, api_context: APIRequestContext):
        resp = api_context.get("/api/v1/dashboard/insights")
        assert resp.ok
        body = resp.json()
        assert "insights" in body
        assert "trends" in body


class TestScrapeAPI:
    def test_list_scrape_runs(self, api_context: APIRequestContext):
        resp = api_context.get("/api/v1/scrape/runs")
        assert resp.ok
        body = resp.json()
        assert isinstance(body, list)
        if body:
            run = body[0]
            assert "source_id" in run
            assert "status" in run
            assert "items_scraped" in run

    def test_trigger_scrape_no_match(self, api_context: APIRequestContext):
        """Triggering with a non-existent scraper key returns no_sources."""
        resp = api_context.post("/api/v1/scrape/run", data={"sources": ["nonexistent_scraper"]})
        assert resp.ok
        body = resp.json()
        assert body["status"] == "no_sources"


class TestAnalysisAPI:
    def test_trigger_analysis(self, api_context: APIRequestContext):
        resp = api_context.post("/api/v1/analysis/run")
        assert resp.ok
        body = resp.json()
        assert body["status"] == "started"
