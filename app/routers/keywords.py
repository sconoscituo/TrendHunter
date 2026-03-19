from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List

from app.database import get_db
from app.models.keyword import Keyword
from app.models.user import User
from app.utils.auth import get_current_active_user

router = APIRouter(prefix="/api/keywords", tags=["keywords"])


class KeywordCreate(BaseModel):
    keyword: str
    category: Optional[str] = None
    is_alert_enabled: bool = False
    alert_threshold: int = 70
    note: Optional[str] = None


class KeywordUpdate(BaseModel):
    category: Optional[str] = None
    is_alert_enabled: Optional[bool] = None
    alert_threshold: Optional[int] = None
    note: Optional[str] = None


@router.post("/", summary="키워드 저장", status_code=status.HTTP_201_CREATED)
async def create_keyword(
    body: KeywordCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """트렌드 모니터링할 키워드를 저장합니다."""
    # 중복 확인
    result = await db.execute(
        select(Keyword).where(
            Keyword.user_id == current_user.id,
            Keyword.keyword == body.keyword,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="이미 저장된 키워드입니다.")

    kw = Keyword(
        user_id=current_user.id,
        keyword=body.keyword,
        category=body.category,
        is_alert_enabled=body.is_alert_enabled,
        alert_threshold=body.alert_threshold,
        note=body.note,
    )
    db.add(kw)
    await db.commit()
    await db.refresh(kw)
    return {"message": "키워드가 저장되었습니다.", "id": kw.id, "keyword": kw.keyword}


@router.get("/", summary="내 키워드 목록 조회")
async def list_keywords(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """저장된 키워드 목록을 반환합니다."""
    result = await db.execute(
        select(Keyword)
        .where(Keyword.user_id == current_user.id)
        .order_by(Keyword.created_at.desc())
    )
    keywords = result.scalars().all()
    return {
        "total": len(keywords),
        "keywords": [
            {
                "id": k.id,
                "keyword": k.keyword,
                "category": k.category,
                "is_alert_enabled": k.is_alert_enabled,
                "alert_threshold": k.alert_threshold,
                "note": k.note,
                "created_at": k.created_at.isoformat(),
            }
            for k in keywords
        ],
    }


@router.patch("/{keyword_id}", summary="키워드 설정 수정")
async def update_keyword(
    keyword_id: int,
    body: KeywordUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Keyword).where(Keyword.id == keyword_id, Keyword.user_id == current_user.id)
    )
    kw = result.scalar_one_or_none()
    if not kw:
        raise HTTPException(status_code=404, detail="키워드를 찾을 수 없습니다.")

    if body.category is not None:
        kw.category = body.category
    if body.is_alert_enabled is not None:
        kw.is_alert_enabled = body.is_alert_enabled
    if body.alert_threshold is not None:
        kw.alert_threshold = body.alert_threshold
    if body.note is not None:
        kw.note = body.note

    await db.commit()
    return {"message": "키워드 설정이 업데이트되었습니다.", "id": kw.id}


@router.delete("/{keyword_id}", summary="키워드 삭제")
async def delete_keyword(
    keyword_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Keyword).where(Keyword.id == keyword_id, Keyword.user_id == current_user.id)
    )
    kw = result.scalar_one_or_none()
    if not kw:
        raise HTTPException(status_code=404, detail="키워드를 찾을 수 없습니다.")
    await db.delete(kw)
    await db.commit()
    return {"message": "키워드가 삭제되었습니다."}
