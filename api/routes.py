from fastapi import APIRouter, HTTPException, status

from api.models import GenerateCreativesRequest
from api.services import generate_creatives
from src.modeling.creative import CreativeResponse

router = APIRouter(prefix="/api/v1", tags=["creatives"])


@router.post(
    "/generate-creatives",
    response_model=CreativeResponse,
    status_code=status.HTTP_200_OK,
)
def generate_creatives_endpoint(request: GenerateCreativesRequest) -> CreativeResponse:
    try:
        return generate_creatives(request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Creative generation failed.")
