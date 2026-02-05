"""Slack character creation app."""

from __future__ import annotations


def main() -> None:
    """Start the Slack app. Socket Mode if app_token is set, HTTP otherwise."""
    import logging

    from config import settings
    from slack_app.app import create_app

    app = create_app()
    # Set the App's own logger to DEBUG so the SDK instance-level checks pass
    app.logger.setLevel(logging.DEBUG)

    if settings.slack_app_token:
        from slack_bolt.adapter.socket_mode import SocketModeHandler

        handler = SocketModeHandler(
            app,
            settings.slack_app_token,
            all_message_trace_enabled=True,
        )
        handler.start()
    else:
        app.start(port=3000)
