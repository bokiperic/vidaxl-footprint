import datetime
from sqlalchemy import Date, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class Article(Base):
    __tablename__ = "articles"
    __table_args__ = (UniqueConstraint("source_id", "external_id", name="uq_article_source_external"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    external_id: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(10), nullable=True)
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    topics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    source = relationship("Source", back_populates="articles")
