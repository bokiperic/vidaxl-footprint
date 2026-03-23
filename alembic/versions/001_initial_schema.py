"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=False),
        sa.Column("region", sa.String(10), nullable=True),
        sa.Column("scraper_key", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
    )

    op.create_table(
        "scrape_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), server_default="running"),
        sa.Column("items_scraped", sa.Integer(), server_default="0"),
        sa.Column("cursor_state", postgresql.JSONB(), nullable=True),
    )

    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("author", sa.String(255), nullable=True),
        sa.Column("rating", sa.Numeric(2, 1), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("review_date", sa.Date(), nullable=True),
        sa.Column("product_name", sa.Text(), nullable=True),
        sa.Column("product_category", sa.Text(), nullable=True),
        sa.Column("sentiment", sa.String(10), nullable=True),
        sa.Column("sentiment_score", sa.Float(), nullable=True),
        sa.Column("topics", postgresql.JSONB(), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(), nullable=True),
        sa.UniqueConstraint("source_id", "external_id", name="uq_review_source_external"),
    )

    op.create_table(
        "articles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("author", sa.String(255), nullable=True),
        sa.Column("published_date", sa.Date(), nullable=True),
        sa.Column("sentiment", sa.String(10), nullable=True),
        sa.Column("sentiment_score", sa.Float(), nullable=True),
        sa.Column("topics", postgresql.JSONB(), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(), nullable=True),
        sa.UniqueConstraint("source_id", "external_id", name="uq_article_source_external"),
    )

    op.create_table(
        "analysis_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), server_default="running"),
        sa.Column("mode", sa.String(20), server_default="mock"),
        sa.Column("reviews_analyzed", sa.Integer(), server_default="0"),
    )

    op.create_table(
        "analysis_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("analysis_run_id", sa.Integer(), sa.ForeignKey("analysis_runs.id"), nullable=False),
        sa.Column("result_type", sa.String(50), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("data", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Seed default sources
    op.execute("""
        INSERT INTO sources (name, source_type, base_url, region, scraper_key) VALUES
        ('Trustpilot UK', 'review_platform', 'https://www.trustpilot.com/review/vidaxl.co.uk', 'GB', 'trustpilot'),
        ('Trustpilot DE', 'review_platform', 'https://www.trustpilot.com/review/vidaxl.de', 'DE', 'trustpilot'),
        ('Trustpilot NL', 'review_platform', 'https://www.trustpilot.com/review/vidaxl.nl', 'NL', 'trustpilot'),
        ('Trustpilot DK', 'review_platform', 'https://www.trustpilot.com/review/vidaxl.dk', 'DK', 'trustpilot'),
        ('Trustpilot NO', 'review_platform', 'https://www.trustpilot.com/review/vidaxl.no', 'NO', 'trustpilot'),
        ('Trustpilot ES', 'review_platform', 'https://www.trustpilot.com/review/vidaxl.es', 'ES', 'trustpilot'),
        ('Trustpilot FR', 'review_platform', 'https://www.trustpilot.com/review/vidaxl.fr', 'FR', 'trustpilot'),
        ('Trustpilot IE', 'review_platform', 'https://www.trustpilot.com/review/vidaxl.ie', 'IE', 'trustpilot'),
        ('Trustpilot AU', 'review_platform', 'https://www.trustpilot.com/review/vidaxl.com.au', 'AU', 'trustpilot'),
        ('Trustpilot COM', 'review_platform', 'https://www.trustpilot.com/review/vidaxl.com', NULL, 'trustpilot'),
        ('Trustpilot IT', 'review_platform', 'https://www.trustpilot.com/review/vidaxl.it', 'IT', 'trustpilot'),
        ('Trustpilot SE', 'review_platform', 'https://www.trustpilot.com/review/vidaxl.se', 'SE', 'trustpilot'),
        ('Trustpilot FI', 'review_platform', 'https://www.trustpilot.com/review/vidaxl.fi', 'FI', 'trustpilot'),
        ('Reviews.io', 'review_platform', 'https://www.reviews.io/company-reviews/store/vidaxl.co.uk', 'GB', 'reviewsio'),
        ('PissedConsumer', 'review_platform', 'https://www.pissedconsumer.com/vidaxl.html', NULL, 'pissedconsumer'),
        ('VidaXL Blog', 'news', 'https://corporate.vidaxl.com/blog', NULL, 'news_generic')
    """)


def downgrade() -> None:
    op.drop_table("analysis_results")
    op.drop_table("analysis_runs")
    op.drop_table("articles")
    op.drop_table("reviews")
    op.drop_table("scrape_runs")
    op.drop_table("sources")
