from api.models import GenerateCreativesRequest
from src.modeling.creative import Creative, CreativeResponse

_MOCK_CLUSTERS = ["awareness", "conversion", "retention"]

_MOCK_IMAGE_URL = "https://cdn.example.com/mock-ad.png"


def generate_creatives(request: GenerateCreativesRequest) -> CreativeResponse:
    """
    Mock creative generation. Replace with real AI pipeline calls.
    Produces one Creative per cluster.
    """
    creatives = [
        Creative(
            image_url=_MOCK_IMAGE_URL,
            prompt=(
                f"A compelling {cluster} ad for {request.product_name} "
                f"priced at {request.price}. "
                f"Highlights: {', '.join(request.benefits[:2])}."
            ),
            cluster=cluster,
            strategy={
                "objective": cluster,
                "tone": "professional",
                "format": "static_banner",
            },
            metadata={
                "product_name": request.product_name,
                "price": request.price,
                "ingredients": request.ingredients,
            },
        )
        for cluster in _MOCK_CLUSTERS
    ]

    return CreativeResponse.from_list(creatives)
