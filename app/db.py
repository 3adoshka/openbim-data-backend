from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, Integer, JSON, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from app.config import settings
from app.schemas import ModelIngestionReport

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class ModelRevisionORM(Base):
    __tablename__ = "model_revisions"
    revision_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False)
    storage_uri: Mapped[str] = mapped_column(String(512), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    total_products: Mapped[int] = mapped_column(Integer, nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False)
    report_json: Mapped[dict] = mapped_column(JSON, nullable=False)

def init_db() -> None:
    Base.metadata.create_all(bind=engine)

def save_revision(db: Session, report: ModelIngestionReport, storage_uri: str) -> None:
    db.merge(ModelRevisionORM(revision_id=report.revision_id, filename=report.filename, schema_version=report.schema_version, storage_uri=storage_uri, ingested_at=report.ingested_at, total_products=report.total_products, quality_score=report.quality_score, report_json=report.model_dump(mode="json")))
    db.commit()

def load_revision(db: Session, revision_id: str) -> ModelIngestionReport | None:
    row = db.get(ModelRevisionORM, revision_id)
    return ModelIngestionReport.model_validate(row.report_json) if row else None

def list_revision_ids(db: Session) -> list[str]:
    return [r[0] for r in db.query(ModelRevisionORM.revision_id).order_by(ModelRevisionORM.ingested_at.desc()).all()]
