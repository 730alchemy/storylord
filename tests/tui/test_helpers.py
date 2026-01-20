"""Helper functions for TUI rendering tests."""

from typing import TYPE_CHECKING

from textual.widget import Widget

if TYPE_CHECKING:
    from textual.pilot import Pilot


def get_rendered_text(widget: Widget) -> str:
    """Extract plain text from widget's renderable.

    Args:
        widget: The widget to extract text from.

    Returns:
        Plain text content of the widget.
    """
    try:
        # Try to get renderable and extract plain text
        if hasattr(widget, "renderable") and widget.renderable:
            if hasattr(widget.renderable, "plain"):
                return widget.renderable.plain
            # If renderable is a string, return it
            if isinstance(widget.renderable, str):
                return widget.renderable
        # Try render() method
        if hasattr(widget, "render"):
            rendered = widget.render()
            if hasattr(rendered, "plain"):
                return rendered.plain
            if isinstance(rendered, str):
                return rendered
        # Fallback: try to get text from common widget properties
        if hasattr(widget, "text"):
            return widget.text
        if hasattr(widget, "value"):
            return str(widget.value)
        if hasattr(widget, "content"):
            return str(widget.content)
    except Exception:
        pass
    return ""


def get_screen_text(pilot: "Pilot") -> str:
    """Get all visible text from rendered screen.

    Args:
        pilot: The Textual pilot instance.

    Returns:
        Plain text content of the entire screen.
    """
    try:
        # Render the app screen
        screen_render = pilot.app.render()
        if hasattr(screen_render, "plain"):
            return screen_render.plain
        if isinstance(screen_render, str):
            return screen_render
        # Try to get text from the current screen
        if hasattr(pilot.app, "screen") and pilot.app.screen:
            screen = pilot.app.screen
            # Collect text from all widgets recursively
            return _collect_widget_text(screen)
    except Exception:
        pass
    return ""


def _collect_widget_text(widget: Widget) -> str:
    """Recursively collect text from widget and its children.

    Args:
        widget: The widget to collect text from.

    Returns:
        Combined text from widget and children.
    """
    texts = []

    # Get text from this widget
    widget_text = get_rendered_text(widget)
    if widget_text:
        texts.append(widget_text)

    # Get text from children
    if hasattr(widget, "children"):
        for child in widget.children:
            child_text = _collect_widget_text(child)
            if child_text:
                texts.append(child_text)

    return "\n".join(texts)


def assert_text_visible(
    pilot: "Pilot", text: str, case_sensitive: bool = False
) -> None:
    """Assert that text appears in rendered output.

    Args:
        pilot: The Textual pilot instance.
        text: The text to search for.
        case_sensitive: Whether search should be case sensitive.

    Raises:
        AssertionError: If text is not found.
    """
    screen_text = get_screen_text(pilot)
    if not case_sensitive:
        screen_text = screen_text.lower()
        text = text.lower()

    if text not in screen_text:
        # Try to get more context for debugging
        widget_texts = []
        try:
            if hasattr(pilot.app, "screen") and pilot.app.screen:
                screen = pilot.app.screen
                for widget in screen.query("*"):
                    widget_text = get_rendered_text(widget)
                    if widget_text:
                        widget_texts.append(
                            f"{widget.__class__.__name__}: {widget_text[:100]}"
                        )
        except Exception:
            pass

        error_msg = f"Text '{text}' not found in rendered screen.\n"
        error_msg += f"Screen text (first 500 chars): {screen_text[:500]}\n"
        if widget_texts:
            error_msg += f"Widget texts: {widget_texts[:10]}"
        raise AssertionError(error_msg)


def assert_widget_visible(
    widget: Widget, min_height: int = 1, min_width: int = 1
) -> None:
    """Assert that a widget is visible and has meaningful dimensions.

    Args:
        widget: The widget to check.
        min_height: Minimum expected height in terminal lines. Defaults to 1.
        min_width: Minimum expected width in terminal columns. Defaults to 1.

    Raises:
        AssertionError: If widget is hidden or too small.
    """
    if not widget.display:
        raise AssertionError(f"Widget {widget} display is False")

    if not widget.visible:
        raise AssertionError(f"Widget {widget} visible is False")

    # Check dimensions
    # .region includes layout position and size
    if widget.region.height < min_height:
        raise AssertionError(
            f"Widget {widget} height {widget.region.height} is less than minimum {min_height}"
        )

    if widget.region.width < min_width:
        raise AssertionError(
            f"Widget {widget} width {widget.region.width} is less than minimum {min_width}"
        )


async def wait_for_text(
    pilot: "Pilot", text: str, timeout: float = 2.0, case_sensitive: bool = False
) -> bool:
    """Wait for text to appear in rendered output.

    Args:
        pilot: The Textual pilot instance.
        text: The text to wait for.
        timeout: Maximum time to wait in seconds.
        case_sensitive: Whether search should be case sensitive.

    Returns:
        True if text appeared, False if timeout.
    """
    import asyncio

    start_time = asyncio.get_event_loop().time()
    while True:
        screen_text = get_screen_text(pilot)
        if not case_sensitive:
            screen_text = screen_text.lower()
            search_text = text.lower()
        else:
            search_text = text

        if search_text in screen_text:
            return True

        elapsed = asyncio.get_event_loop().time() - start_time
        if elapsed >= timeout:
            return False

        await pilot.pause(0.1)
        await asyncio.sleep(0.05)


def get_widget_text_by_id(pilot: "Pilot", widget_id: str) -> str:
    """Get rendered text from a widget by its ID.

    Args:
        pilot: The Textual pilot instance.
        widget_id: The ID of the widget to query.

    Returns:
        Plain text content of the widget, or empty string if not found.
    """
    try:
        if hasattr(pilot.app, "screen") and pilot.app.screen:
            screen = pilot.app.screen
            widget = screen.query_one(f"#{widget_id}", default=None)
            if widget:
                return get_rendered_text(widget)
    except Exception:
        pass
    return ""
