"""
Tool registry — defines tools exposed to the Claude agent and maps them to handlers.

To add a new system (e.g. Meta Ads):
  1. Add tool definition(s) to TOOLS list
  2. Add handler(s) to TOOL_HANDLERS dict
  Nothing else needs to change.
"""

from agent.tools.creative_tools import generate_prompts, generate_creative, lookup_product

# ---------------------------------------------------------------------------
# Tool Definitions (Anthropic tool_use format)
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "generate_prompts",
        "description": (
            "Generate creative scene prompts for all 5 ad clusters "
            "(product_first, solution_first, doctor_first, ingredient_first, problem_first). "
            "Returns prompts grouped by cluster so the user can pick which ones to turn into images."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_name":   {"type": "string", "description": "Name of the product"},
                "brand_name":     {"type": "string", "description": "Brand or company name"},
                "category":       {"type": "string", "description": "Product category (e.g. Health Supplement, Skincare)"},
                "benefits":       {"type": "array",  "items": {"type": "string"}, "description": "Up to 5 product benefits"},
                "problems":       {"type": "array",  "items": {"type": "string"}, "description": "Up to 3 problems the product solves"},
                "solutions":      {"type": "array",  "items": {"type": "string"}, "description": "Up to 3 solutions offered"},
                "ingredients":    {"type": "array",  "items": {"type": "string"}, "description": "Up to 5 key ingredients"},
                "price":          {"type": "string", "description": "Price of the product (e.g. ₹499)"},
                "offer":          {"type": "string", "description": "Current offer or discount (e.g. 20% off)"},
                "num_variations": {"type": "integer","description": "Number of prompt variations per cluster (default 5)", "default": 5},
                "product_image":  {"type": "string", "description": "File path to product image (optional)"},
                "person_image":   {"type": "string", "description": "File path to person/model image (optional)"},
            },
            "required": ["product_name", "brand_name", "category", "benefits", "problems", "solutions", "ingredients", "price", "offer"],
        },
    },
    {
        "name": "lookup_product",
        "description": (
            "Search product memory for a previously used product by name. "
            "Call this as soon as the user provides a product name to check if we have saved data. "
            "If found, present the saved fields to the user and ask if they want to autofill."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_name": {"type": "string", "description": "Product name to search for"},
            },
            "required": ["product_name"],
        },
    },
    {
        "name": "generate_creative",
        "description": (
            "Generate final ad images from user-selected prompts. "
            "Takes the prompts the user chose from generate_prompts and produces actual images."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "selected_prompts": {
                    "type": "object",
                    "description": (
                        "Dict mapping cluster names to list of selected prompt strings. "
                        "Example: {\"product_first\": [\"close-up macro shot...\"], \"solution_first\": [\"lifestyle scene...\"]}"
                    ),
                },
            },
            "required": ["selected_prompts"],
        },
    },
]

# ---------------------------------------------------------------------------
# Handler Map
# ---------------------------------------------------------------------------

TOOL_HANDLERS = {
    "lookup_product":    lookup_product,
    "generate_prompts":  generate_prompts,
    "generate_creative": generate_creative,
}


def execute_tool(name: str, inputs: dict) -> dict:
    """Dispatch a tool call to its handler. Returns a result dict."""
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return {"status": "error", "message": f"Unknown tool: {name}"}
    try:
        return handler(**inputs)
    except Exception as e:
        return {"status": "error", "message": str(e)}
