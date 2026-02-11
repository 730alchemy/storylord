"""Slack character creation app."""

from __future__ import annotations


def main() -> None:
    """Start the Slack app. Socket Mode if app_token is set, HTTP otherwise."""
    from config import get_settings
    from slack_app.app import create_app

    app = create_app()
    settings = get_settings()

    if settings.slack_app_token:
        from slack_bolt.adapter.socket_mode import SocketModeHandler

        handler = SocketModeHandler(app, settings.slack_app_token)
        handler.start()
    else:
        app.start(port=3000)
