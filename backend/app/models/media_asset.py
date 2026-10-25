"""MediaAsset model: persistent records for Cloudinary uploaded media assets.

Persists authoritative references to media assets managed in Cloudinary:
- Associated with Opportunities (event posters, promotional flyers, schedules)
- Associated with EventSignal Legacy records (event memories, handovers, documentation)
- Associated with Institutional Workspaces with strict tenant isolation

Security requirements:
- Cloudinary public_id is preserved as the immutable identity of the asset.
- Tenant isolation: institution_id scoping guarantees cross-college privacy.
- Cloudinary private credentials never touch client-side storage or database rows.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_id

if TYPE_CHECKING:
    from app.models.event_memory import EventMemory
    from app.models.institution import Institution
    from app.models.legacy_handover import LegacyHandover
    from app.models.opportunity import Opportunity
    from app.models.user import User


class MediaAsset(TimestampMixin, Base):
    __tablename__ = "media_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)

    # Cloudinary asset identifiers
    cloudinary_public_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    secure_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(32), default="image", nullable=False)
    format: Mapped[str | None] = mapped_column(String(16), nullable=True)
    bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Metadata & presentation
    alt_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_purpose: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True, default="opportunity_poster"
    )

    # Security & isolation
    institution_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    uploader_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Entity associations
    opportunity_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("opportunities.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    event_memory_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("event_memories.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    legacy_handover_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("legacy_handovers.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    is_verified: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    extra_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    institution: Mapped[Institution | None] = relationship("Institution")
    uploader: Mapped[User] = relationship("User")
    opportunity: Mapped[Opportunity | None] = relationship(
        "Opportunity", back_populates="media_assets"
    )
    event_memory: Mapped[EventMemory | None] = relationship(
        "EventMemory", back_populates="media_assets"
    )
    legacy_handover: Mapped[LegacyHandover | None] = relationship(
        "LegacyHandover", back_populates="media_assets"
    )
