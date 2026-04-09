"""
Core agentic loop — Groq (Llama 3.3-70B) with tool/function calling.
Groq uses the OpenAI-compatible API format for tool calls.
"""

import json
import os
import re
from dataclasses import dataclass, field

from groq import Groq, BadRequestError
from dotenv import load_dotenv

from agent.system_prompt import SYSTEM_PROMPT
from agent.tool_registry import TOOLS, execute_tool

load_dotenv()

# Primary model + fallback for tool_use_failed errors
_PRIMARY_MODEL  = "llama-3.3-70b-versatile"
_FALLBACK_MODEL = "mixtral-8x7b-32768"


# ---------------------------------------------------------------------------
# Convert Anthropic-style tool definitions → OpenAI/Groq format
# ---------------------------------------------------------------------------
def _to_groq_tools(tools: list) -> list:
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["input_schema"],
            },
        }
        for t in tools
    ]


_GROQ_TOOLS = _to_groq_tools(TOOLS)


def _clean_tool_arguments(raw: str) -> str:
    """
    Fix common JSON issues produced by Llama when generating tool call arguments:
    - Escaped apostrophes  (\\'  →  ')
    - Single-quoted strings  →  double-quoted strings
    """
    # Remove backslash-escaped apostrophes (e.g. "Dr Bimal\'s" → "Dr Bimal's")
    cleaned = raw.replace("\\'", "'")
    return cleaned


def _parse_tool_arguments(raw: str) -> dict:
    """Parse tool call arguments, cleaning common Llama JSON artefacts."""
    cleaned = _clean_tool_arguments(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Last resort: remove all backslash escapes before apostrophes
        fallback = re.sub(r"\\(?=')", "", cleaned)
        try:
            return json.loads(fallback)
        except json.JSONDecodeError:
            return {}


@dataclass
class AgentResponse:
    """Structured response returned to the UI after each agent turn."""
    text: str
    cluster_prompts: dict = field(default_factory=dict)
    images: list = field(default_factory=list)
    awaiting_approval: bool = False
    approval_payload: dict = field(default_factory=dict)
    campaign_context: dict = field(default_factory=dict)


class AdAgent:
    """
    Stateful conversational agent backed by Groq Llama 3.3-70B.
    Falls back to Mixtral on tool_use_failed errors.
    One instance per user session.
    """

    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model  = _PRIMARY_MODEL
        self.conversation_history: list[dict] = []
        self._pending_images: list[dict] = []

    def reset(self):
        self.conversation_history = []
        self._pending_images = []
        self.model = _PRIMARY_MODEL  # reset to primary on new conversation

    def chat(self, user_message: str) -> AgentResponse:
        """
        Send a user message, run the agentic loop, return a structured response.
        Loops until the model stops calling tools.
        """
        self.conversation_history.append({
            "role": "user",
            "content": user_message,
        })

        cluster_prompts: dict = {}
        images: list = []
        campaign_context: dict = {}

        while True:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": SYSTEM_PROMPT}] + self.conversation_history,
                    tools=_GROQ_TOOLS,
                    tool_choice="auto",
                    max_tokens=4096,
                )
            except BadRequestError as e:
                # Groq returns 400 tool_use_failed when Llama produces invalid JSON
                # in the tool call arguments — switch to fallback model and retry once
                if "tool_use_failed" in str(e) and self.model != _FALLBACK_MODEL:
                    print(f"[Agent] tool_use_failed on {self.model} — retrying with {_FALLBACK_MODEL}")
                    self.model = _FALLBACK_MODEL
                    # Remove the last user message and re-append so history stays clean
                    # (the failed assistant turn was never appended)
                    continue
                raise

            message       = response.choices[0].message
            finish_reason = response.choices[0].finish_reason

            # Build assistant history entry
            assistant_msg: dict = {
                "role":    "assistant",
                "content": message.content or "",
            }
            if message.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id":   tc.id,
                        "type": "function",
                        "function": {
                            "name":      tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in message.tool_calls
                ]
            self.conversation_history.append(assistant_msg)

            if finish_reason == "tool_calls" and message.tool_calls:
                for tc in message.tool_calls:
                    # Parse arguments — handles escaped apostrophes and other artefacts
                    inputs = _parse_tool_arguments(tc.function.arguments)

                    result = execute_tool(tc.function.name, inputs)

                    if tc.function.name == "generate_prompts" and result.get("status") == "success":
                        cluster_prompts = result.get("cluster_prompts", {})
                        campaign_context = {
                            k: v for k, v in inputs.items()
                            if k not in ("num_variations", "product_image", "person_image")
                        }

                    if tc.function.name == "generate_creative" and result.get("status") == "success":
                        images = result.get("images", [])
                        self._pending_images = images

                    self.conversation_history.append({
                        "role":         "tool",
                        "tool_call_id": tc.id,
                        "content":      json.dumps(result),
                    })

            else:
                text             = message.content or ""
                awaiting_approval = bool(images)
                approval_payload  = {"images": images} if images else {}

                return AgentResponse(
                    text=text,
                    cluster_prompts=cluster_prompts,
                    images=[img["path"] for img in images],
                    awaiting_approval=awaiting_approval,
                    approval_payload=approval_payload,
                    campaign_context=campaign_context,
                )
