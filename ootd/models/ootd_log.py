from datetime import datetime, date
from sqlalchemy import String, DateTime, Date, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON
from database import Base

class OotdLog(Base):
    """OOTDログエンティティ"""
    __tablename__ = "ootd_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, default=date.today)
    weather: Mapped[str] = mapped_column(String(20), nullable=True)
    season: Mapped[str] = mapped_column(String(20), nullable=True)
    memo: Mapped[str] = mapped_column(Text, nullable=True)
    snapshot_path: Mapped[str] = mapped_column(String(255), nullable=False)
    clothing_ids: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now
    )

    def to_dict(self) -> dict:
        import json
        return {
            "id": self.id,
            "date": self.date.strftime("%Y-%m-%d"),
            "weather": self.weather,
            "season": self.season,
            "memo": self.memo,
            "snapshot_path": self.snapshot_path,
            "clothing_ids": json.loads(self.clothing_ids),
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M"),
        }