"""Server-only credentials and independently versioned task profiles."""
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class AIConfiguration(Base):
    __tablename__ = 'ai_configurations'
    purpose: Mapped[str] = mapped_column(String(20), primary_key=True)
    provider: Mapped[str] = mapped_column(String(30))
    model: Mapped[str] = mapped_column(String(200))
    encrypted_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    use_environment: Mapped[int] = mapped_column(Integer, default=0)
    max_output_tokens: Mapped[int] = mapped_column(Integer, default=8192)
    version: Mapped[int] = mapped_column(Integer, default=1)
