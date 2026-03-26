"""add tavily web search sources

Revision ID: 002
Revises: 001
Create Date: 2026-03-26

"""
from typing import Sequence, Union

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO sources (name, source_type, base_url, region, scraper_key) VALUES
        ('Web Search - Brand Mentions', 'web_search', 'Hunkemöller brand reputation news', NULL, 'tavily_search'),
        ('Web Search - News & Press', 'web_search', 'Hunkemöller news press release', NULL, 'tavily_search'),
        ('Web Search - Reddit Reviews', 'web_search', 'Hunkemöller review experience', NULL, 'tavily_reviews'),
        ('Web Search - Complaints', 'web_search', 'Hunkemöller complaint problem', NULL, 'tavily_reviews')
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM sources WHERE scraper_key IN ('tavily_search', 'tavily_reviews')
    """)
