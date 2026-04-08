"""
Core agentic loop — Groq (Llama 3.3-70B) with tool/function calling.
Groq uses the OpenAI-compatible API format for tool calls.
"""

import json
import os
from dataclasses import dataclass, field

from groq import Groq
from dotenv import load_dotenv

from agent.system_prompt import SYSTEM_PROMPT
from agent.tool_registry import TOOLS, execute_tool

load_dotenv()


# ---------------------------------------------------------------------------
# Convert Anthropic-style tool definitions → OpenAI/Groq format
# Anthropic: {"name": ..., "description": ..., "input_schema": {...}}
# OpenAI:    {"type": "function", "function": {"name": ..., "description": ..., "parameters": {...}}}
# ---------------------------------------------------------------------------
def _to_groq_tools(tools: list) -> list:
    groq_tools = []
    for t in tools:
        groq_tools.append({
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["input_schema"],
            },
        })
    return groq_tools


_GROQ_TOOLS = _to_groq_tools(TOOLS)


@dataclass
class AgentResponse:
    """Structured response returned to the UI after each agent turn."""
    text: str
    cluster_prompts: dict = field(default_factory=dict)
    images: list = field(default_factory=list)
    awaiting_approval: bool = False
    approval_payload: dict = field(default_factory=dict)
    # Campaign fields collected by the agent (product_name, brand_name, etc.)
    # Populated whenever generate_prompts or generate_creative is called
    campaign_context: dict = field(default_factory=dict)


class AdAgent:
    """
    Stateful conversational agent backed by Groq Llama 3.3-70B.
    One instance per user session.
    """

    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
        self.conversation_history: list[dict] = []
        self._pending_images: list[dict] = []

    def reset(self):
        self.conversation_history = []
        self._pending_images = []

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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": SYSTEM_PROMPT}] + self.conversation_history,
                tools=_GROQ_TOOLS,
                tool_choice="auto",
                max_tokens=4096,
            )

            message = response.choices[0].message
            finish_reason = response.choices[0].finish_reason

            # Append assistant message to history
            assistant_msg: dict = {
                "role": "assistant",
                "content": message.content or "",
            }
            if message.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in message.tool_calls
                ]
            self.conversation_history.append(assistant_msg)

            if finish_reason == "tool_calls" and message.tool_calls:
                # Execute each tool call
                for tc in message.tool_calls:
                    try:
                        inputs = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        inputs = {}

                    result = execute_tool(tc.function.name, inputs)

                    if tc.function.name == "generate_prompts" and result.get("status") == "success":
                        cluster_prompts = result.get("cluster_prompts", {})
                        # Capture campaign fields from tool inputs
                        campaign_context = {k: v for k, v in inputs.items()
                                            if k not in ("num_variations", "product_image", "person_image")}

                    if tc.function.name == "generate_creative" and result.get("status") == "success":
                        images = result.get("images", [])
                        self._pending_images = images

                    # Feed result back as a tool message
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result),
                    })

            else:
                # Model is done — return final text
                text = message.content or ""

                awaiting_approval = bool(images)
                approval_payload = {"images": images} if images else {}

                return AgentResponse(
                    text=text,
                    cluster_prompts=cluster_prompts,
                    images=[img["path"] for img in images],
                    awaiting_approval=awaiting_approval,
                    approval_payload=approval_payload,
                    campaign_context=campaign_context,
                )
