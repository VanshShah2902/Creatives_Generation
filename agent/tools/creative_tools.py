"""
Wraps the generative_ads_ai pipeline for use as agent tools.
"""

import json
import os
import sys
import time

# Ensure project root is on path so pipeline imports work
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from generation_engine.pipeline_runner import AdGenerationPipeline

_pipeline: AdGenerationPipeline | None = None


def _get_pipeline() -> AdGenerationPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = AdGenerationPipeline()
    return _pipeline


def generate_prompts(
    product_name: str,
    brand_name: str,
    category: str,
    benefits: list,
    problems: list,
    solutions: list,
    ingredients: list,
    price: str,
    offer: str,
    num_variations: int = 5,
    product_image: str = "",
    person_image: str = "",
) -> dict:
    """
    Runs the prompt generation stage of the pipeline.
    Returns all cluster prompts grouped by cluster so the user can select.

    Returns:
        {
            "status": "success",
            "cluster_prompts": {
                "product_first": ["prompt1", "prompt2", ...],
                "solution_first": [...],
                ...
            }
        }
    """
    campaign = _build_campaign_json(
        product_name, brand_name, category, benefits, problems,
        solutions, ingredients, price, offer, product_image, person_image
    )
    input_path = _save_campaign(campaign)

    pipeline = _get_pipeline()
    all_clusters = ["product_first", "solution_first", "doctor_first", "ingredient_first", "problem_first"]

    cluster_prompts = pipeline.run(input_path, num_variations=num_variations)

    # Retry any clusters that failed silently (Groq rate-limit during sequential calls)
    missing = [c for c in all_clusters if c not in cluster_prompts]
    if missing:
        print(f"[creative_tools] Retrying missing clusters after 5s: {missing}")
        time.sleep(5)
        retry_result = pipeline.run(input_path, num_variations=num_variations)
        for c in missing:
            if c in retry_result:
                cluster_prompts[c] = retry_result[c]
                print(f"[creative_tools] Retry succeeded for {c}")
            else:
                print(f"[creative_tools] Retry also failed for {c} — skipping")

    # Persist the merged result
    prompts_file = os.path.join("outputs", "prompts", "cluster_prompts.json")
    with open(prompts_file, "w") as f:
        json.dump(cluster_prompts, f, indent=4)

    return {
        "status": "success",
        "cluster_prompts": cluster_prompts,
    }


def generate_creative(selected_prompts: dict) -> dict:
    """
    Runs image generation for user-selected prompts.
    selected_prompts format: {"product_first": ["chosen prompt text"], ...}

    Returns:
        {
            "status": "success",
            "images": [
                {"path": "outputs/generated_ads/product_first.png", "cluster": "product_first"},
                ...
            ]
        }
    """
    # Write selected prompts to the file the pipeline reads
    selected_path = os.path.join("outputs", "prompts", "selected_prompts.json")
    os.makedirs(os.path.dirname(selected_path), exist_ok=True)
    with open(selected_path, "w") as f:
        json.dump(selected_prompts, f, indent=4)

    pipeline = _get_pipeline()
    pipeline.generate_from_selected()

    # Collect generated image paths
    ads_dir = os.path.join("outputs", "generated_ads")
    images = []
    for cluster in selected_prompts:
        prompts = selected_prompts[cluster]
        if isinstance(prompts, str):
            prompts = [prompts]
        for i in range(len(prompts)):
            suffix = f"_{i+1}" if len(prompts) > 1 else ""
            fname = f"{cluster}{suffix}.png"
            fpath = os.path.join(ads_dir, fname)
            if os.path.exists(fpath):
                images.append({"path": fpath, "cluster": cluster})

    return {
        "status": "success",
        "images": images,
    }


def lookup_product(product_name: str) -> dict:
    """
    Search product memory for a product by name (case-insensitive partial match).
    Returns the matched product fields so the agent can offer autofill to the user.

    Returns:
        {"status": "found", "product": {...}}   if a match is found
        {"status": "not_found"}                 if no match
    """
    import sys, os
    _ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if _ROOT not in sys.path:
        sys.path.insert(0, _ROOT)

    from src.memory.product_memory import ProductMemory
    memory = ProductMemory()
    all_products = memory.get_all_products()

    search = product_name.lower().strip()
    for p in all_products:
        if search in p.get("product_name", "").lower():
            # Return only the fields needed for campaign generation
            return {
                "status": "found",
                "product": {
                    "product_name":  p.get("product_name", ""),
                    "brand_name":    p.get("brand_name", ""),
                    "category":      p.get("category", ""),
                    "benefits":      p.get("benefits", p.get("benefit_points", [])),
                    "problems":      p.get("problems", []),
                    "solutions":     p.get("solutions", []),
                    "ingredients":   p.get("ingredients", []),
                    "price":         p.get("price", ""),
                    "offer":         p.get("offer", ""),
                    "product_image": p.get("product_image", ""),
                    "person_image":  p.get("person_image", ""),
                },
            }

    return {"status": "not_found"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_campaign_json(
    product_name, brand_name, category, benefits, problems,
    solutions, ingredients, price, offer, product_image, person_image
) -> dict:
    return {
        "product_name": product_name,
        "brand_name": brand_name,
        "category": category,
        "benefits": benefits[:5],
        "problems": problems[:3],
        "solutions": solutions[:3],
        "ingredients": ingredients[:5],
        "price": price,
        "offer": offer,
        "product_image": product_image,
        "person_image": person_image,
        "creative_type": "standard",
    }


def _save_campaign(campaign: dict) -> str:
    os.makedirs("inputs", exist_ok=True)
    path = os.path.join("inputs", "campaign_input.json")
    with open(path, "w") as f:
        json.dump(campaign, f, indent=4)
    return path
