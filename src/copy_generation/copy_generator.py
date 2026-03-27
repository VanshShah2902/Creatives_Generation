from src.llm.groq_client import GroqClient
import json
import re

class CopyGenerator:
    def __init__(self):
        self.llm = GroqClient()

    def generate_copy(self, payload: dict) -> dict:
        product = payload.get("product_name", "")
        benefits = payload.get("benefits", [])
        problems = payload.get("problems", [])
        ingredients = payload.get("ingredients", [])
        cluster = payload.get("cluster_id", payload.get("creative_style", ""))

        prompt = f"""
        You are an expert ad copywriter.

        Generate a high-converting advertisement copy.

        PRODUCT: {product}
        BENEFITS: {benefits}
        PROBLEMS: {problems}
        INGREDIENTS: {ingredients}
        AD TYPE: {cluster}

        RULES:
        - Headline must be short, bold, attention-grabbing
        - Subheadline must support benefits clearly
        - Subheadline must be maximum 6-10 words
        - Must be short, punchy, and benefit-driven
        - Avoid long sentences
        - Avoid generic phrases like "best product"
        - Make it sound like real ad copy
        - Tone depends on AD TYPE:
          - product_first: premium, product-focused
          - solution_first: problem-solution tone
          - doctor_first: authority, trust
          - ingredient_first: natural, purity

        OUTPUT JSON:
        {{
            "headline": "...",
            "subheadline": "..."
        }}
        
        Return ONLY valid JSON. Do NOT include any explanation or text outside JSON. Do NOT wrap in markdown or backticks.
        """

        print("[Groq] Generating prompt + copy...")
        try:
            response = self.llm.generate(prompt)
            
            # Cleaning Response logic
            response = response.strip()

            # Remove markdown code blocks
            if response.startswith("```"):
                response = response.split("```")[1]

            # Remove 'json' label if present
            response = response.replace("json", "").strip()

            print("[CopyGenerator] Cleaned Response:", response[:300])

            copy = json.loads(response)
            
            subheadline = copy.get("subheadline", "")
            
            # Hard truncate if too long
            words = subheadline.split()
            if len(words) > 10:
                subheadline = " ".join(words[:10])
                copy["subheadline"] = subheadline
                
            return copy
        except Exception as e:
            print("[CopyGenerator ERROR]:", e)
            print("[CopyGenerator RAW]:", response)
            # Fallback (as before but with more logs)
            return {
                "headline": payload.get("product_name", "Premium Product"),
                "subheadline": "Supports your health naturally."
            }
