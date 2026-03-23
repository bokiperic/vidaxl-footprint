from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    source_type: Mapped[str] = mapped_column(String(50))
    base_url: Mapped[str] = mapped_column(Text)
    region: Mapped[str | None] = mapped_column(String(10), nullable=True)
    scraper_key: Mapped[str] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    reviews = relationship("Review", back_populates="source")
    articles = relationship("Article", back_populates="source")
    scrape_runs = relationship("ScrapeRun", back_populates="source")
