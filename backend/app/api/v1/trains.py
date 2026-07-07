from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.deps import get_db
from ...schemas import TrainClassDetail, TrainClassList
from ...services import TrainService

router = APIRouter(prefix="/trains", tags=["trains"])


@router.get("/classes", response_model=list[TrainClassList])
async def list_train_classes(db: AsyncSession = Depends(get_db)):
    svc = TrainService(db)
    classes = await svc.list_classes()
    return [
        TrainClassList(
            id=str(c.id),
            name=c.name,
            max_speed_kmh=c.max_speed_kmh,
            acceleration_ms2=c.acceleration_ms2,
            deceleration_ms2=c.deceleration_ms2,
            length_m=c.length_m,
            capacity_seated=c.capacity_seated,
            capacity_standing=c.capacity_standing,
        )
        for c in classes
    ]


@router.get("/classes/{class_id}", response_model=TrainClassDetail)
async def get_train_class(class_id: str, db: AsyncSession = Depends(get_db)):
    svc = TrainService(db)
    c = await svc.get_class(class_id)
    if not c:
        from ...core.exceptions import NotFoundError

        raise NotFoundError(f"Train class {class_id} not found")
    return TrainClassDetail(
        id=str(c.id),
        name=c.name,
        max_speed_kmh=c.max_speed_kmh,
        acceleration_ms2=c.acceleration_ms2,
        deceleration_ms2=c.deceleration_ms2,
        length_m=c.length_m,
        capacity_seated=c.capacity_seated,
        capacity_standing=c.capacity_standing,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )
