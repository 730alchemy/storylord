"""Simile Smasher editor implementation for storylord."""

from __future__ import annotations

import structlog
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

from models import EditedText, EditorInput
from tools.registry import ToolRegistry

log = structlog.get_logger(__name__)


SYSTEM_PROMPT = """Follow these guidelines to improve text
- Do not modify any dialogue
- Find all similes in the text and convert them to direct metaphors. A simile compares two things using "like" or "as" (e.g., "Her eyes were like stars"). A metaphor states that one thing IS another (e.g., "Her eyes were stars").
- If a sentence uses a form of the verb "to be" (e.g. "is", "was", "are"), generate an alternative of the sentence that retains the same meaning and uses an action verb

Make only necessary changes. Do not change text that is lies outside the guidelines defined above. Do not change any dialogue"""


USER_PROMPT_TEMPLATE = """{text}"""


class SimileSmasherEditor:
    """Editor that replaces similes with direct metaphors.

    This editor finds similes (comparisons using "like" or "as") and
    converts them into direct metaphors for more impactful prose.
    """

    name = "simile-smasher"

    def edit(
        self,
        input: EditorInput,
        tools: ToolRegistry | None = None,
    ) -> EditedText:
        """Replace similes with metaphors in the given text.

        Args:
            input: The editor input containing text to edit.
            tools: Optional tool registry (not used by this editor).

        Returns:
            The text with similes converted to metaphors.
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
