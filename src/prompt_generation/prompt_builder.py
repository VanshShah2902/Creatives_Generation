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

# ---------------------------------------------------------------------------
# Competitor-intelligence-derived winning patterns
# Based on analysis of OZiva, Woolah, Plix, Kapiva ads + our own winning ads
# ---------------------------------------------------------------------------

# Winning color palettes per cluster (derived from competitor + winning ad analysis)
CLUSTER_COLORS = {
    "product_first": [
        ("deep green", "white", "gold"),
        ("dark green", "cream", "white"),
        ("forest green", "white", "dark brown"),
        ("olive green", "white", "earth tones"),
    ],
    "solution_first": [
        ("forest green", "cream", "gold"),
        ("maroon", "cream", "forest green"),
        ("deep green", "beige", "white"),
        ("teal", "cream", "yellow"),
    ],
    "doctor_first": [
        ("maroon", "cream", "forest green"),
        ("navy blue", "white", "forest green"),
        ("deep green", "white", "red"),
        ("white", "deep green", "dark brown"),
    ],
    "ingredient_first": [
        ("deep green", "earth tones", "white"),
        ("white", "deep green", "tan"),
        ("forest green", "white", "brown"),
        ("dark green", "white", "black"),
    ],
    "problem_first": [
        ("vibrant red", "dark green", "beige"),
        ("red", "beige", "dark green"),
        ("maroon", "cream", "forest green"),
        ("vibrant red", "fatty yellow", "dark green"),
    ],
}

# Hook type cycling per variation — drives the compositional intent of each ad
# Derived from winning patterns: fear, benefit, authority, problem, curiosity
CLUSTER_HOOK_CYCLES = {
    "product_first":    ["benefit", "curiosity", "authority", "benefit", "curiosity"],
    "solution_first":   ["benefit", "relief", "authority", "benefit", "relief"],
    "doctor_first":     ["authority", "trust", "authority", "trust", "benefit"],
    "ingredient_first": ["curiosity", "benefit", "authority", "curiosity", "benefit"],
    "problem_first":    ["fear", "problem", "fear", "problem", "fear"],
}

# Winning visual patterns per cluster (from competitor analysis)
# Each cluster has 5 visual pattern signals — one per variation
CLUSTER_VISUAL_PATTERNS = {
    "product_first": [
        "product elevated on plain background with dramatic rim lighting, clean white space, minimal elements",
        "product as central hero surrounded by soft ingredient halos, lifestyle context blurred in background",
        "product macro close-up filling 60% of frame, ingredient raw elements scattered naturally around it",
        "product in soft glow-effect circle, feature benefit list on the left side, plain background",
        "dramatic product shot with medical-grade clean aesthetic, dark background with product illuminated",
    ],
    "solution_first": [
        "vertical split: left side shows solution text in bold, right side product as glowing hero answer",
        "product hero centered, solution outcome text floating above in large bold type, lifestyle context",
        "before-after vertical split: dark tense left, bright hopeful right with product as the turning point",
        "product in spotlight circle, solution benefit statements radiating outward as visual anchors",
        "lifestyle scene showing positive transformation, product prominently anchored at bottom-right",
    ],
    "doctor_first": [
        "doctor face as primary emotional trust anchor taking 50% of frame, product on desk in foreground",
        "doctor in white coat pointing to product, clinical background, credential badge visible",
        "split: doctor recommendation quote on left in large serif, product hero on right with glow",
        "doctor holding product at eye level, direct eye contact, clean clinical background, trust focus",
        "scientific diagram or ingredient chart in background, doctor and product in foreground as authority",
    ],
    "ingredient_first": [
        "top-down flat lay: product centered, raw ingredients symmetrically arranged around it on natural surface",
        "ingredient macro shots in grid formation with product center-bottom, botanical aesthetic",
        "ingredient sourcing story: raw herbs and botanical elements flowing into product shot, earthy background",
        "product hero with ingredient pills or capsules spilling naturally, each ingredient labeled",
        "ingredient symmetry: product in center glow circle, key ingredients positioned at cardinal points",
    ],
    "problem_first": [
        "macro medical illustration of artery or heart taking 70% of frame, product anchored at bottom with urgency text",
        "split composition: left side shows person with visible distress, right side shows product as the clear answer",
        "bold problem statement in large red text dominating upper frame, product as the solution below",
        "dramatic close-up of person's concerned face, problem text overlay, product in corner as hope",
        "visual metaphor showing blockage or health risk (anatomical), product positioned as the solution",
    ],
}

# Emotion to facial expression mapping (specific, not abstract)
EMOTION_EXPRESSIONS = {
    "fear":       "person's face showing genuine fear and worry, furrowed brows, tense jaw",
    "panic":      "person showing visible panic, wide eyes, tense posture, hand on chest",
    "worry":      "person expressing quiet concern, troubled eyes, slightly pursed lips",
    "shock":      "person showing shock and disbelief, raised eyebrows, open mouth",
    "relief":     "person showing deep relief, eyes closing softly, shoulders dropping, warm smile",
    "calm":       "person with calm, serene expression, soft eyes, relaxed posture",
    "hope":       "person with hopeful, uplifted expression, gentle smile, looking upward",
    "trust":      "doctor or expert showing confident, reassuring expression, direct eye contact",
    "confidence": "person with strong, assured posture, direct gaze, slight smile",
    "premium":    "person with sophisticated, discerning expression, poised posture",
    "freshness":  "person showing energized, refreshed expression, bright eyes, natural smile",
    "natural":    "person with relaxed, wholesome expression, genuine warm smile",
    "urgency":    "person showing urgent concern, pointing or gesturing toward the problem",
}

# Background type per cluster (from competitor analysis — plain wins most)
CLUSTER_BACKGROUND = {
    "product_first":    ["plain", "gradient", "plain"],
    "solution_first":   ["plain", "gradient", "real_scene"],
    "doctor_first":     ["plain", "plain", "gradient"],
    "ingredient_first": ["real_scene", "plain", "real_scene"],
    "problem_first":    ["plain", "gradient", "plain"],
}


class PromptBuilder:
    """
    Converts structured campaign payload into high-fidelity image generation prompts.
    Built on competitor intelligence from OZiva, Woolah, Plix, Kapiva analysis
    and our own winning ad patterns.
    """

    CLUSTER_SCENES = {
        "product_first": {
            "composition": "product as undisputed hero, large and central, commanding the entire frame",
            "subject_positions": "product centered and elevated, maximum breathing space around it"
        },
        "solution_first": {
            "composition": "split layout: solution or positive outcome text dominates the left, product as the hero answer on the right",
            "subject_positions": "product on right as the glowing hero answer, solution text prominently on left, clear visual contrast between problem state and answered solution"
        },
        "doctor_first": {
            "composition": "doctor as primary trust anchor on the right, benefit points on the left, high-impact authority headline at top",
            "subject_positions": "doctor on right facing camera, product on desk in foreground, clear space reserved for headline"
        },
        "ingredient_first": {
            "composition": "product centered with ingredient grid layout, ingredients radiating outward",
            "subject_positions": "product at center in glow circle, key ingredients arranged symmetrically around it"
        },
        "problem_first": {
            "environment": "real-life discomfort setting, slightly tense and urgent atmosphere",
            "camera": "eye-level emotional storytelling shot",
            "lighting": "slightly dramatic, soft shadow lighting with urgency",
            "subject_positions": "left side shows the problem statement in bold red text overlay, right side shows the product as the clear solution",
            "props": "subtle lifestyle elements indicating health discomfort"
        }
    }

    # 5 variation styles — each one drives a different visual approach
    VARIATIONS = [
        "close-up macro product shot, bright high-key lighting, clean clinical mood",
        "wide angle lifestyle scene, warm natural sunlight, relatable human environment",
        "top-down flat lay, natural daylight, organic botanical mood",
        "eye-level premium product shot, soft diffused lighting, minimal luxury feel",
        "dramatic angled shot, high contrast lighting, bold attention-grabbing urgency",
    ]

    def build_prompt_core(self, cluster_id: str) -> str:
        c_scene = self.CLUSTER_SCENES.get(cluster_id, self.CLUSTER_SCENES["product_first"])
        comp = c_scene.get("composition", "focused structured composition")
        pos  = c_scene.get("subject_positions", "subject clearly visible")
        return f"{comp}, {pos}"

    def build_multiple_prompts(self, payload, cluster_id, blueprint=None, strategy=None, num_variations=5):
        print("[PromptBuilder] Building prompts for cluster:", cluster_id)
        prompts = []

        product_name = payload.get("product_name", "product")
        benefits     = payload.get("benefits", [])
        solutions    = payload.get("solutions", [])
        problems     = payload.get("problems", [])
        ingredients  = payload.get("ingredients", [])
        price        = payload.get("price", "")
        category     = payload.get("category", "")

        # Load emotions for this cluster
        from src.config.config_loader import load_emotions
        EMOTION_CONFIG = load_emotions()
        cluster_emotions = EMOTION_CONFIG.get(cluster_id, ["confidence"])

        # Strategy overrides
        headline_tone = strategy.get("headline_tone") if strategy else "informative"

        # Precompute: which variations feature a woman (2-3 of 5)
        num_woman = random.choice([2, 3])
        use_woman_indices = set(random.sample(range(num_variations), k=min(num_woman, num_variations)))

        # Hook cycle for this cluster
        hook_cycle = CLUSTER_HOOK_CYCLES.get(cluster_id, ["benefit"] * 5)

        # Visual patterns for this cluster
        visual_patterns = CLUSTER_VISUAL_PATTERNS.get(cluster_id, ["product as hero"] * 5)

        # Winning color palettes for this cluster
        color_options = CLUSTER_COLORS.get(cluster_id, [("deep green", "white", "gold")])

        for i, variation in enumerate(self.VARIATIONS[:num_variations]):
            emotion   = random.choice(cluster_emotions)
            hook_type = hook_cycle[i % len(hook_cycle)]
            print(f"[PromptBuilder][Variation {i}] Emotion: {emotion} | Hook: {hook_type}")

            components = []

            # ── 1. Variation style (sets lighting + camera mood) ──────────────
            components.append(variation)

            # ── 2. Core scene structural signal ──────────────────────────────
            components.append(self.build_prompt_core(cluster_id))

            # ── 3. Winning visual pattern for this variation ──────────────────
            components.append(visual_patterns[i % len(visual_patterns)])

            # ── 4. Blueprint environment only (NOT lighting — variation sets that) ──
            if blueprint:
                env = blueprint.get("environment", "")
                if env:
                    components.append(f"environment setting: {env}")

            # ── 5. Subject strategy ──────────────────────────────────────────
            if cluster_id == "doctor_first":
                components.append("featuring a professional Indian doctor in white coat as subject, authoritative and reassuring")
            elif cluster_id == "problem_first":
                # problem_first always has a person showing the problem
                components.append("featuring a natural looking middle-aged Indian person showing health distress")
            elif i in use_woman_indices:
                components.append("featuring a natural looking Indian middle-aged woman in the scene, relatable and expressive")
            else:
                components.append("product-focused scene, no human subject, emphasizing product clarity and brand authority")

            # ── 6. Product name ───────────────────────────────────────────────
            components.append(f"featuring {product_name}")

            # ── 7. Benefits (randomized 3) ────────────────────────────────────
            if benefits:
                selected = random.sample(benefits, min(3, len(benefits)))
                components.append(f"key highlights: {', '.join(selected)}")

            # ── 8. Cluster-specific content injection ─────────────────────────

            # solution_first: inject user's solutions
            if cluster_id == "solution_first" and solutions:
                selected_solutions = random.sample(solutions, min(2, len(solutions)))
                components.append(f"solutions featured prominently: {', '.join(selected_solutions)}")
                components.append("visual emphasis on the positive outcome and transformation")

            # ingredient_first: inject ingredients
            if cluster_id == "ingredient_first" and ingredients:
                selected_ings = random.sample(ingredients, min(3, len(ingredients)))
                components.append(f"featuring key ingredients: {', '.join(selected_ings)}, ingredients visually arranged around product in a botanical composition")

            # problem_first: inject user's specific problems
            if cluster_id == "problem_first":
                if problems:
                    problem_text = random.choice(problems)
                    components.append(f"bold left-side text overlay: '{problem_text}'")
                    components.append("right side: product shown as the direct, clear solution to the stated problem")
                components.append("person showing visible discomfort, health concern, tense posture and expressive worried face")
                components.append("headline framed as a direct problem statement, emotionally urgent and relatable")

            # ── 9. Price (if provided) ────────────────────────────────────────
            if price:
                components.append(f"price: {price}")

            # ── 10. Hook type compositional signal ────────────────────────────
            hook_signals = {
                "fear":      "fear-based hook, urgent warning tone, medical authority, alarming visual anchor",
                "benefit":   "benefit-led hook, clear outcome promise, aspirational and positive visual",
                "curiosity": "curiosity hook, open question or knowledge gap visual, viewer wants to know more",
                "authority": "authority hook, scientific credibility, doctor or expert validation visual",
                "problem":   "problem identification hook, relatable pain point, viewer sees themselves in it",
                "relief":    "relief hook, positive transformation, stress lifting, hopeful outcome visual",
                "trust":     "trust hook, credibility signals, clean professional aesthetic, proof elements",
            }
            components.append(hook_signals.get(hook_type, "benefit-led hook"))

            # ── 11. Emotion with specific facial expression ───────────────────
            expression = EMOTION_EXPRESSIONS.get(emotion, f"subject expressing {emotion}")
            components.append(expression)

            # ── 12. Winning color palette (competitor-intelligence-derived) ───
            color_pick = random.choice(color_options)
            primary, secondary, accent = color_pick
            components.append(f"color scheme: {primary} as primary, {secondary} as secondary, {accent} as accent — high contrast, clear visual hierarchy")

            # ── 13. Background type ───────────────────────────────────────────
            bg_options = CLUSTER_BACKGROUND.get(cluster_id, ["plain"])
            bg_type = bg_options[i % len(bg_options)]
            if bg_type == "plain":
                components.append("clean plain background, no distracting elements, product and subject as sole focus")
            elif bg_type == "gradient":
                components.append("smooth gradient background, soft color transition, modern premium feel")
            else:
                components.append("real-life contextual background, slightly blurred for depth of field")

            # ── 14. Typography signals ────────────────────────────────────────
            if cluster_id == "problem_first" or emotion in ("fear", "panic", "urgency", "shock"):
                font_preset = next((p for p in FONT_PRESETS if p["name"] == "panic"), FONT_PRESETS[0])
            elif emotion in ("calm", "relief", "hope", "natural"):
                font_preset = next((p for p in FONT_PRESETS if p["name"] == "calm"), FONT_PRESETS[0])
            elif cluster_id == "doctor_first" or emotion in ("trust", "confidence", "authority"):
                font_preset = next((p for p in FONT_PRESETS if p["name"] == "trust"), FONT_PRESETS[0])
            else:
                font_preset = FONT_PRESETS[i % len(FONT_PRESETS)]

            print("[FontPreset]", font_preset["name"])
            components.append(f"headline text: {font_preset['headline']}")
            components.append(f"supporting text: {font_preset['sub']}")
            components.append(f"CTA text: {font_preset['cta']}")
            components.append("clean professional typography hierarchy, high readability, low text density, text does not overwhelm the visual")

            # ── 15. Headline tone ─────────────────────────────────────────────
            components.append(f"headline tone: {headline_tone}, emotionally resonant, concise and punchy")

            # ── 16. Quality and format modifiers ─────────────────────────────
            components.extend([
                "clear visual hierarchy, single focal point, no cluttered elements",
                "clean advertisement composition",
                "1:1 square format",
                "no distortion, balanced layout",
                "8k resolution, ultra realistic, photographic quality",
            ])

            # Join and clean up
            prompt = ", ".join(c for c in components if c.strip())
            while ", ," in prompt:
                prompt = prompt.replace(", ,", ",")

            prompts.append(sanitize_prompt(prompt))
            print(f"[PromptBuilder] Variation {i} built ({len(prompt)} chars)")

        return prompts
