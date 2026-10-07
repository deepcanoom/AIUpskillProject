"""Base class for AI agents."""

import json
import os
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Tuple

from litellm import completion
import litellm

# Maps a LiteLLM provider prefix to the env vars that can hold its API key.
# LiteLLM model strings look like "<provider>/<model>" — e.g.
# "anthropic/claude-3-5-sonnet-20241022", "gemini/gemini-3.7-flash".
# A model string with no prefix ("claude-haiku-4-5-20251001") is left to
# LiteLLM to resolve, which is why this lookup can legitimately return None.
PROVIDER_KEY_ENV_VARS: Dict[str, Tuple[str, ...]] = {
    "anthropic": ("ANTHROPIC_API_KEY",),
    "gemini": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    "groq": ("GROQ_API_KEY",),
    "openai": ("OPENAI_API_KEY",),
    "mistral": ("MISTRAL_API_KEY",),
    "cohere": ("COHERE_API_KEY",),
}


def describe_llm_error(exc: Exception) -> str:
    """
    Turn a raw LiteLLM exception into an actionable hint.

    LiteLLM's messages are long provider payloads; this surfaces the one
    thing the developer actually needs to change.
    """
    name = type(exc).__name__
    text = str(exc)

    if "RateLimit" in name or "429" in text:
        return (
            f"{name}: provider rate/quota limit reached.\n"
            "  • Free tiers are small (Gemini: 20 requests/day/model; "
            "Groq: ~30 requests/minute).\n"
            "  • Re-run with fewer articles: "
            "python src/complete_pipeline.py --limit 5\n"
            "  • Or switch LITELLM_MODEL in .env to a provider with headroom."
        )

    if "Authentication" in name or "invalid_api_key" in text:
        return (
            f"{name}: the API key was rejected by the provider.\n"
            "  • Check that LITELLM_MODEL matches the key you set in .env.\n"
            "  • Anthropic console keys (sk-ant-usr-...) are not scoped to a "
            "workspace and will not work."
        )

    if "NotFound" in name:
        return (
            f"{name}: the provider does not recognise that model.\n"
            "  • The model string is likely retired; pick a current one from "
            "https://docs.litellm.ai/docs/providers"
        )

    return f"{name}: {text[:200]}"


def is_retryable_error(exc: Exception) -> bool:
    """
    Decide whether retrying the same call could plausibly succeed.

    Auth failures, unknown models and exhausted daily quotas are all
    deterministic — retrying them only wastes time and quota.
    """
    name = type(exc).__name__
    if any(tag in name for tag in ("Authentication", "NotFound", "BadRequest")):
        return False

    text = str(exc)
    if "RESOURCE_EXHAUSTED" in text or "quota" in text.lower():
        return False
    if "invalid x-api-key" in text or "invalid_api_key" in text:
        return False

    return True


class BaseAgent(ABC):
    """
    Base class for all AI agents.

    Implements Template Method pattern:
    - execute() orchestrates the workflow
    - Subclasses implement specific steps
    """

    def __init__(
        self,
        model: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
    ):
        """
        Initialize agent.

        Args:
            model: LiteLLM model string.
                   Defaults to LITELLM_MODEL from environment.
            tools: Optional list of tool schemas available to the LLM.
        """
        self.model = model or os.getenv("LITELLM_MODEL")

        if not self.model:
            raise ValueError(
                "No model configured. Set LITELLM_MODEL in .env "
                "or pass `model=` to the agent constructor."
            )

        self.tools = tools or []
        self.tool_functions: Dict[str, Callable] = {}

    def _resolve_api_key(self) -> Optional[str]:
        """
        Resolve the API key that matches this agent's model provider.

        LiteLLM forwards whatever `api_key` we hand it, so passing the wrong
        provider's key produces a confusing auth error (e.g. sending a Gemini
        key to Anthropic yields "invalid x-api-key"). Looking the key up by
        provider keeps `LITELLM_MODEL` and its key in sync automatically.

        Returns:
            The key for the model's provider, or None if the model has no
            recognized prefix — in that case LiteLLM resolves it itself.
        """
        provider = self.model.split("/", 1)[0].lower()
        for env_var in PROVIDER_KEY_ENV_VARS.get(provider, ()):
            key = os.getenv(env_var)
            if key:
                return key
        return None

    def _validate_llm_config(self) -> None:
        """
        Fail fast with an actionable message when the provider key is missing.

        Without this, the first LLM call dies deep in LiteLLM with a generic
        authentication error and the real cause is hard to spot.
        """
        provider = self.model.split("/", 1)[0].lower()
        expected = PROVIDER_KEY_ENV_VARS.get(provider)
        if expected and not self._resolve_api_key():
            raise ValueError(
                f"No API key found for provider {provider!r} "
                f"(model {self.model!r}).\n"
                f"Set one of: {', '.join(expected)} in your .env file."
            )

    async def execute(
        self,
        input_path: str,
        output_path: str,
    ) -> Dict[str, Any]:
        """
        Execute agent workflow.

        Steps:
        1. Load input context
        2. Process with LLM
        3. Save results

        Args:
            input_path: Path to input file.
            output_path: Path where output will be saved.

        Returns:
            Execution metadata.
        """
        print(f"\n🤖 {self.__class__.__name__} starting...")

        # Fail fast on a missing/mismatched provider key, before spending
        # time loading context or burning tokens on retries.
        self._validate_llm_config()

        # Step 1: Load context
        context = await self._load_context(input_path)

        # Step 2: Process context
        result = await self._process(context)

        # Step 3: Save result
        await self._save_result(result, output_path)

        print(f"✅ {self.__class__.__name__} complete")

        return {
            "input_path": input_path,
            "output_path": output_path,
            "success": True,
        }

    @abstractmethod
    async def _load_context(
        self,
        input_path: str,
    ) -> Dict[str, Any]:
        """
        Load input context.

        Subclasses must implement this method.
        """
        pass

    @abstractmethod
    async def _process(
        self,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Process context.

        Subclasses must implement this method.
        """
        pass

    @abstractmethod
    async def _save_result(
        self,
        result: Dict[str, Any],
        output_path: str,
    ) -> None:
        """
        Save processing result.

        Subclasses must implement this method.
        """
        pass

    def _call_llm(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Call the configured LLM through LiteLLM.

        Args:
            prompt: User prompt.
            system: Optional system prompt.
            max_tokens: Optional cap on generated tokens. Worth setting on
                every call: providers meter output tokens per minute, and an
                uncapped call can request far more than the task needs and
                trip the limit.

        Returns:
            LLM response text.
        """
        messages = []

        if system:
            messages.append(
                {
                    "role": "system",
                    "content": system,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        try:
            # Resolve the key from the model's own provider so switching
            # LITELLM_MODEL never requires editing this file.
            response = completion(
                model=self.model,
                messages=messages,
                api_key=self._resolve_api_key(),
                max_tokens=max_tokens,
            )

            return response.choices[0].message.content

        except Exception as exc:
            print(f"❌ LLM call failed: {exc}")
            raise

    def register_tool_function(
        self,
        name: str,
        function: Callable,
    ) -> None:
        """
        Register the Python function that implements a tool.

        Args:
            name: Tool name.
            function: Python function backing the tool.
        """
        self.tool_functions[name] = function

    def _call_llm_with_tools(
        self,
        prompt: str,
        system: Optional[str] = None,
    ) -> str:
        """
        Call the LLM with tool support.

        Process:
        1. Send prompt and available tools to the LLM.
        2. Check whether the LLM requests a tool.
        3. Execute the requested Python function.
        4. Return the tool result to the LLM.
        5. Repeat until the LLM produces a final text response.

        Maximum tool-call rounds: 10.
        """
        messages: List[Dict] = []

        if system:
            messages.append(
                {
                    "role": "system",
                    "content": system,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        api_key = self._resolve_api_key()

        # Protect against infinite tool-call loops.
        for _ in range(10):
            try:
                response = completion(
                    model=self.model,
                    messages=messages,
                    tools=self.tools or None,
                    api_key=api_key,
                )
            except Exception as exc:
                print(f"❌ LLM tool call failed: {exc}")
                raise

            msg = response.choices[0].message

            # No tool calls means the model returned its final answer.
            if not getattr(msg, "tool_calls", None):
                return msg.content

            # Record the assistant message before tool results.
            messages.append(msg.model_dump())

            # Execute every tool requested by the model.
            for tool_call in msg.tool_calls:
                name = tool_call.function.name

                args = json.loads(tool_call.function.arguments or "{}")

                print(f"   🔧 Tool call: {name}({args})")

                if name not in self.tool_functions:
                    raise ValueError(f"Tool {name!r} not registered")

                tool_function = self.tool_functions[name]

                result = tool_function(**args)

                print(f"   📊 Tool result: {result}")

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": name,
                        "content": json.dumps(result),
                    }
                )

        raise RuntimeError(
            "Tool-call loop exceeded 10 rounds. " "The model may be stuck."
        )
