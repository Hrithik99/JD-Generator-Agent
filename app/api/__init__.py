from fastapi import APIRouter

from app.api.draft import router as draft_router
from app.api.final import router as final_router
from app.api.feedback import router as feedback_router
from app.api.approve import router as approve_router  # NEW

router = APIRouter()
router.include_router(draft_router)
router.include_router(final_router)
router.include_router(feedback_router)
router.include_router(approve_router)  # NEW
