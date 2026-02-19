"""Blueprint model - Requirements 2.1, 2.3"""
from typing import Optional
from sqlalchemy import String, Integer, Text, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin


class Blueprint(Base, TimestampMixin):
    """
    Blueprint model representing a version-controlled WorkSpaces Custom Bundle image template.
    
    Requirements:
    - 2.1: Blueprint storage in version control system
    - 2.3: Version immutability - new versions preserve previous versions
    """
    __tablename__ = "blueprints"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    
    # Blueprint identification
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Description and metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # AWS WorkSpaces Custom Bundle ID
    bundle_id: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Team-scoped access control (Requirement 2.4)
    team_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Configuration and metadata
    configuration: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    # Version control metadata
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_version_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    
    # Relationships
    workspaces: Mapped[list["WorkSpace"]] = relationship(
        "WorkSpace",
        back_populates="blueprint"
    )
    
    # Ensure name + version is unique per team
    __table_args__ = (
        UniqueConstraint('name', 'version', 'team_id', name='uq_blueprint_name_version_team'),
    )
    
    def __repr__(self) -> str:
        return f"<Blueprint(id={self.id}, name={self.name}, version={self.version})>"
