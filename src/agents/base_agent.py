"""Base class for AI agents."""

import json
import os
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

from litellm import completion


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
    ) -> str:
        """
        Call the configured LLM through LiteLLM.

        Args:
            prompt: User prompt.
            system: Optional system prompt.

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
            response = completion(
                model=self.model,
                messages=messages,
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

        # Protect against infinite tool-call loops.
        for _ in range(10):
            try:
                response = completion(
                    model=self.model,
                    messages=messages,
                    tools=self.tools or None,
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
