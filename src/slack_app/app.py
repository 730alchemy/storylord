"""Bolt app setup and event/command registration."""

from __future__ import annotations

from slack_bolt import App

from agents.discovery import discover_character_agent_types
from config import settings
from slack_app.handlers.commands import handle_create_character
from slack_app.handlers.messages import handle_message
from slack_app.handlers.submissions import handle_modal_1_submit, handle_modal_2_submit
from slack_app.modals import build_agent_properties_modal, build_character_setup_modal
from slack_app.state import StateManager

# Shared state manager — one instance for the lifetime of the process
state_manager = StateManager()


def create_app() -> App:
    """Create and configure the Bolt App with all registered handlers."""
    app = App(
        signing_secret=settings.slack_signing_secret,
        token=settings.slack_bot_token,
    )

    @app.command("/create-character")
    def create_character(ack, command):
        handle_create_character(
            ack=ack,
            command=command,
            state_manager=state_manager,
        )

    @app.message()
    def on_message(message, say):
        handle_message(message=message, say=say, state_manager=state_manager)

    @app.action("open_modal_1")
    def on_open_modal_1(ack, body, client):
        ack()
        channel_id = body["channel"]["id"]
        agent_types = discover_character_agent_types()
        client.views_open(
            trigger_id=body["trigger_id"],
            view=build_character_setup_modal(
                agent_types=agent_types, channel_id=channel_id
            ),
        )

    @app.view("modal_1_submit")
    def on_modal_1_submit(ack, view, body, client):
        handle_modal_1_submit(
            ack=ack,
            view=view,
            body=body,
            state_manager=state_manager,
            client=client,
        )

    @app.action("open_modal_2")
    def on_open_modal_2(ack, body, client):
        ack()
        user_id = body["user"]["id"]
        channel_id = body["channel"]["id"]
        state = state_manager.get(user_id)

        if state is None:
            return

        agent_types = discover_character_agent_types()
        agent_type_instance = agent_types[state.agent_type]

        client.views_open(
            trigger_id=body["trigger_id"],
            view=build_agent_properties_modal(
                agent_type=state.agent_type,
                property_schema=agent_type_instance.property_schema,
                channel_id=channel_id,
            ),
        )

    @app.view("modal_2_submit")
    def on_modal_2_submit(ack, view, body, client):
        handle_modal_2_submit(
            ack=ack,
            view=view,
            body=body,
            state_manager=state_manager,
            client=client,
        )

    return app
