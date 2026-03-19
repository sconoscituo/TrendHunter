from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    keyword = Column(String, nullable=False, index=True)
    category = Column(String, nullable=True)          # 카테고리 (예: IT, 패션, 음식 등)
    is_alert_enabled = Column(Boolean, default=False) # 트렌드 알림 여부
    alert_threshold = Column(Integer, default=70)     # 알림 발생 트렌드 점수 임계값 (0~100)
    note = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="keywords")
