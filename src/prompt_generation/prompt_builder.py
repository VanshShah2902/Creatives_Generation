import random

def sanitize_prompt(prompt: str) -> str:
    banned_phrases = [
        "clean split-frame horizontal composition",
        "split-frame composition",
        "dual panel composition"
    ]

    for phrase in banned_phrases:
        prompt = prompt.replace(phrase, "")

    return prompt.strip()

from src.config.config_loader import load_fonts, load_prompts

FONT_CONFIG = load_fonts()
FONT_PRESETS = FONT_CONFIG.get("presets", [])

if not FONT_PRESETS:
    raise ValueError("Font config not loaded")

print("[Config] Fonts Loaded:", len(FONT_PRESETS))

PROMPT_CONFIG = load_prompts()

class PromptBuilder:
    """Converts a structured scene blueprint into a high-fidelity prompt string using variation-first logic."""

    CLUSTER_SCENES = {
        "product_first": {
            "composition": "center large product, top bold headline",
            "subject_positions": "product centered prominently"
        },
        "solution_first": {
            "composition": "left side problem list, right side product",
            "subject_positions": "person on left, product on right"
        },
        "doctor_first": {
            "composition": "right side doctor, left side benefit points, high-impact trust-building headline area at top",
            "subject_positions": "doctor on right, product on desk, clear space reserved for headline text"
        },
        "ingredient_first": {
            "composition": "center product, ingredient grid layout",
            "subject_positions": "product centered, ingredients arranged around"
        },
        "problem_first": {
            "environment": "real-life discomfort setting, slightly tense atmosphere",
            "camera": "eye-level emotional storytelling shot",
            "lighting": "slightly dramatic, soft shadow lighting",
            "subject_positions": "person on left showing problem, empty space for product on right",
            "props": "subtle lifestyle elements indicating discomfort"
        }
    }

    VARIATIONS = [
        "close-up macro product shot, bright high-key lighting, clean clinical mood",
        "wide angle lifestyle scene, warm natural sunlight, relatable environment",
        "top-down ingredient storytelling, natural daylight, organic mood",
        "eye-level premium product shot, soft diffused lighting, minimal luxury feel",
        "dramatic angled shot, high contrast lighting, bold attention-grabbing style"
    ]

    def build_prompt_core(self, cluster_id: str) -> str:
        """Extracts the core scene structural signals."""
        c_scene = self.CLUSTER_SCENES.get(cluster_id, self.CLUSTER_SCENES["product_first"])
        comp = c_scene.get("composition", "focused structured composition")
        pos = c_scene.get("subject_positions", "subject clearly visible")
        return f"{comp}, {pos}"

    def build_multiple_prompts(self, payload, cluster_id, blueprint=None, strategy=None, num_variations=5):
        print("[PromptBuilder] Using Blueprint:", blueprint)
        prompts = []
        cluster_rules = PROMPT_CONFIG.get(cluster_id, {})
        
        core_scene = self.build_prompt_core(cluster_id)
        product_name = payload.get("product_name", "product")
        
        # Load full emotion list for this cluster from config (used per-variation below)
        from src.config.config_loader import load_emotions
        EMOTION_CONFIG = load_emotions()
        cluster_emotions = EMOTION_CONFIG.get(cluster_id, ["neutral"])

        palette = strategy.get("color_palette") if strategy else {}
        headline_tone = strategy.get("headline_tone") if strategy else "informative"
        
        # Step 4: Control Subject Usage (Indian middle-aged woman index selection)
        # Select 2 or 3 indices where the woman will be featured
        use_woman_indices = random.sample(range(num_variations), k=random.choice([2, 3]))

        for i, variation in enumerate(self.VARIATIONS[:num_variations]):
            # Pick a fresh random emotion per variation from the full cluster emotion list
            emotion = random.choice(cluster_emotions)
            print(f"[PromptBuilder][Variation {i}] Emotion: {emotion}")
            components = []
            
            # Step 5: Each prompt must independently decide its components
            
            # 1. Variation Style
            components.append(variation)
            
            # 2. Core Scene Structural Signal
            components.append(core_scene)
            
            # 2a. Blueprint Injection (Environment, Lighting, Camera)
            if blueprint:
                components.append(f"environment: {blueprint.get('environment', '')}")
                components.append(f"lighting: {blueprint.get('lighting', '')}")
                components.append(f"camera style: {blueprint.get('camera_style', '')}")

            # 3. Subject Strategy
            if cluster_id == "doctor_first":
                components.append("featuring a professional doctor as subject")
            elif i in use_woman_indices:
                components.append("featuring a natural looking Indian middle-aged woman in the scene")
            else:
                # Rest remain product-focused as per STEP 4
                components.append("product-focused scene, emphasizing clarity and brand presence, no human subject")

            # 4. Product Name
            components.append(f"featuring {product_name}")

            # 5. Benefits Randomization (STEP 2)
            benefits = payload.get("benefits", [])
            selected_benefits = []
            if benefits:
                selected_benefits = random.sample(benefits, min(3, len(benefits)))
                benefit_text = ", ".join(selected_benefits)
                components.append(f"highlights: {benefit_text}")
                # Optional Debug Log (STEP 6)
                print(f"[PromptBuilder] Selected benefits: {selected_benefits}")

            # 6. Ingredient Randomization (STEP 3)
            selected_ingredients = []
            if cluster_id == "ingredient_first":
                ingredients = payload.get("ingredients", [])
                if ingredients:
                    selected_ingredients = random.sample(ingredients, min(3, len(ingredients)))
                    ingredient_text = ", ".join(selected_ingredients)
                    components.append(f"featuring ingredients such as {ingredient_text}, ingredients visually arranged around product")
                    # Optional Debug Log (STEP 6)
                    print(f"[PromptBuilder] Selected ingredients: {selected_ingredients}")
                else:
                    print(f"[Warning] No ingredients provided for ingredient_first cluster")

            # 7. Pricing
            components.append(f"product price: {payload.get('price', 'rs.599')}")
            
            # Inject emotion for ALL clusters — each variation gets its own random emotion
            components.append(f"subject expressing clear emotion of {emotion}")
            
            if cluster_id == "problem_first":
                print("[Cluster] problem_first active")
                components.append("person showing visible discomfort, worry or stress, tense posture, expressive face")
                components.append("headline phrased as a problem or concern, emotionally triggering")
            
            if palette:
                components.append(
                    f"color scheme using {palette.get('primary')}, {palette.get('secondary')} with {palette.get('accent')} accents"
                )
                
            if cluster_id == "problem_first" or emotion == "panic":
                font_preset = next((p for p in FONT_PRESETS if p["name"] == "panic"), FONT_PRESETS[0])
            elif emotion == "calm":
                font_preset = next((p for p in FONT_PRESETS if p["name"] == "calm"), FONT_PRESETS[4])
            else:
                font_preset = FONT_PRESETS[i % len(FONT_PRESETS)]
                
            print("[FontPreset]", font_preset["name"])
            
            components.append(f"headline text in {font_preset['headline']}")
            components.append(f"supporting text in {font_preset['sub']}")
            components.append(f"call-to-action text in {font_preset['cta']}")
            components.append("clean professional typography hierarchy, high readability, premium ad design")
            
            components.append(
                f"headline tone should feel {headline_tone} and emotionally engaging"
            )
            
            # 8. Fixed Quality Modifiers
            components.extend([
                "clean advertisement composition",
                "1:1 square format",
                "no distortion",
                "balanced layout",
                "8k resolution, ultra realistic"
            ])

            # Join components into final string
            prompt = ", ".join(components)
            
            # Clean up extra commas or accidental double spaces
            while ", ," in prompt:
                prompt = prompt.replace(", ,", ",")
            
            prompts.append(prompt.strip())

        return prompts
