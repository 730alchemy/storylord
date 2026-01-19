"""Default editor implementation for storylord."""

from __future__ import annotations

import structlog
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

from models import EditedText, EditorInput
from tools.registry import ToolRegistry

log = structlog.get_logger(__name__)


SYSTEM_PROMPT = """Improve this text."""


USER_PROMPT_TEMPLATE = """{text}"""


class DefaultEditor:
    """Default editor implementation using Claude Sonnet.

    This editor improves and refines text for clarity, style, and quality.
    """

    name = "default"

    def edit(
        self,
        input: EditorInput,
        tools: ToolRegistry | None = None,
    ) -> EditedText:
        """Edit and improve the given text.

        Args:
            input: The editor input containing text to edit.
            tools: Optional tool registry (not used by default editor).

        Returns:
            The edited and improved text.
        """
        chain = self._create_chain()

        result = chain.invoke({"text": input.text})

        log.info(
            "edit_complete",
            editor=self.name,
            input_length=len(input.text),
            output_length=len(result.text),
        )

        return result

    def _create_chain(self):
        """Create the LangChain chain for editing text."""
        llm = ChatAnthropic(model="claude-sonnet-4-20250514")
        structured_llm = llm.with_structured_output(EditedText)

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                ("user", USER_PROMPT_TEMPLATE),
            ]
        )

        return prompt | structured_llm
