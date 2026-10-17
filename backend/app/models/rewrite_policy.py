"""Administrator-owned character ceilings; separate from researcher-editable paper state."""
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.models.mixins import TimestampMixin


class RewritePolicy(Base, TimestampMixin):
    __tablename__ = 'rewrite_policies'
    scope: Mapped[str] = mapped_column(String(12), primary_key=True)
    target_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mode: Mapped[str] = mapped_column(String(12))
    source_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    discussion_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_by: Mapped[int] = mapped_column(Integer)
