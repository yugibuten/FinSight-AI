from fastapi import APIRouter


router = APIRouter(tags=["System"])


@router.get("/health", summary="Check API health")
def health() -> dict[str, str]:
    return {"status": "ok", "api_version": "v1"}
