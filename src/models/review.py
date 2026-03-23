import datetime
from sqlalchemy import Date, Float, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("source_id", "external_id", name="uq_review_source_external"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    external_id: Mapped[str] = mapped_column(String(255))
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rating: Mapped[float | None] = mapped_column(Numeric(2, 1), nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    product_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    product_category: Mapped[str | None] = mapped_column(Text, nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(10), nullable=True)
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    topics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    source = relationship("Source", back_populates="reviews")
