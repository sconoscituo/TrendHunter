from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from app.utils.auth import get_current_active_user
from app.services.payment import verify_payment, cancel_payment

router = APIRouter(prefix="/api/payments", tags=["payments"])

PLAN_PRICES: dict[str, int] = {"premium": 9900}


class PaymentVerifyRequest(BaseModel):
    imp_uid: str
    merchant_uid: str
    plan: str


class PaymentCancelRequest(BaseModel):
    imp_uid: str
    reason: str = "사용자 요청 취소"


@router.post("/verify", summary="결제 검증 후 구독 업그레이드")
async def verify_and_upgrade(
    body: PaymentVerifyRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    expected_amount = PLAN_PRICES.get(body.plan)
    if expected_amount is None:
        raise HTTPException(status_code=400, detail=f"유효하지 않은 플랜: {body.plan}")

    result = await db.execute(select(Payment).where(Payment.imp_uid == body.imp_uid))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="이미 처리된 결제입니다.")

    is_valid = await verify_payment(body.imp_uid, expected_amount)
    payment = Payment(
        imp_uid=body.imp_uid,
        merchant_uid=body.merchant_uid,
        user_id=current_user.id,
        amount=expected_amount,
        plan=body.plan,
        status=PaymentStatus.PAID if is_valid else PaymentStatus.FAILED,
    )
    db.add(payment)

    if is_valid:
        from app.models.user import PlanType
        current_user.plan = PlanType.PREMIUM
        await db.commit()
        return {"message": "결제 완료. 구독이 업그레이드되었습니다.", "plan": body.plan}

    await db.commit()
    raise HTTPException(status_code=400, detail="결제 검증 실패: 금액 불일치")


@router.post("/cancel", summary="구독 취소 및 환불")
async def cancel_subscription(
    body: PaymentCancelRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Payment).where(
            Payment.imp_uid == body.imp_uid,
            Payment.user_id == current_user.id,
            Payment.status == PaymentStatus.PAID,
        )
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="취소할 결제 내역을 찾을 수 없습니다.")

    await cancel_payment(body.imp_uid, body.reason)
    payment.status = PaymentStatus.CANCELLED
    payment.cancel_reason = body.reason

    from app.models.user import PlanType
    current_user.plan = PlanType.FREE
    await db.commit()
    return {"message": "구독이 취소되고 환불이 처리되었습니다."}


@router.get("/history", summary="결제 내역 조회")
async def get_payment_history(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Payment)
        .where(Payment.user_id == current_user.id)
        .order_by(Payment.created_at.desc())
    )
    payments = result.scalars().all()
    return {
        "total": len(payments),
        "payments": [
            {
                "id": p.id,
                "imp_uid": p.imp_uid,
                "amount": p.amount,
                "plan": p.plan,
                "status": p.status,
                "created_at": p.created_at.isoformat(),
            }
            for p in payments
        ],
    }
