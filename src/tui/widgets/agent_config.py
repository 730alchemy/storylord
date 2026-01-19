"""Agent configuration widget."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Select, Static, TextArea

from agents.discovery import discover_character_agent_types, list_character_agent_types

if TYPE_CHECKING:
    from tui.character_studio import CharacterState


class AgentConfigPane(Vertical):
    """Pane for configuring agent type and properties."""

    def __init__(self, state: "CharacterState") -> None:
        """Initialize the agent config pane.

        Args:
            state: The shared character state.
        """
        super().__init__()
        self.state = state
        self._agent_types = discover_character_agent_types()
        self._property_inputs: dict[str, Input] = {}
        self._refreshing = False  # Flag to prevent re-entrancy during refresh

    def compose(self) -> ComposeResult:
        """Compose the widget layout."""
        yield Static("No character selected", id="agent-status")

        with Vertical(id="agent-form"):
            yield Static("Agent Type:", classes="form-label")

            # Create select options from discovered agent types
            agent_type_options = [
                (name, name) for name in list_character_agent_types()
            ]
            if not agent_type_options:
                agent_type_options = [("default", "default")]

            yield Select(
                agent_type_options,
                id="agent-type-select",
                value=agent_type_options[0][1] if agent_type_options else "default",
            )

            yield Static("Properties:", classes="form-label")
            yield Vertical(id="properties-container")

            yield Static("Agent Instructions:", classes="form-label")
            yield TextArea(id="agent-instructions")

            with Horizontal(classes="button-row"):
                yield Button("Save Agent Config", id="btn-save-agent", variant="primary")

    def on_mount(self) -> None:
        """Initialize the pane when mounted."""
        self._hide_form()
        self.refresh_display()

    def _hide_form(self) -> None:
        """Hide the agent form."""
        form = self.query_one("#agent-form")
        form.display = False

    def _show_form(self) -> None:
        """Show the agent form."""
        form = self.query_one("#agent-form")
        form.display = True

    def refresh_display(self) -> None:
        """Refresh the display from state."""
        profile = self.state.get_selected_profile()
        status = self.query_one("#agent-status", Static)

        if not profile:
            status.update("No character selected")
            self._hide_form()
            return

        status.update(f"Agent config for: {profile.name}")
        self._show_form()

        # Update form fields
        agent_config = profile.agent_config
        if agent_config:
            select = self.query_one("#agent-type-select", Select)
            # Set the value without triggering change event by checking first
            if agent_config.agent_type in [opt[1] for opt in select._options]:
                # Only update if different to avoid unnecessary refresh
                if select.value != agent_config.agent_type:
                    # Temporarily set refreshing flag to prevent on_select_changed from doing anything
                    was_refreshing = self._refreshing
                    self._refreshing = True
                    try:
                        select.value = agent_config.agent_type
                    finally:
                        self._refreshing = was_refreshing
            self.query_one("#agent-instructions", TextArea).text = (
                agent_config.agent_instructions
            )
            # Refresh properties with existing values (this will clear the refreshing flag)
            self._refresh_properties(agent_config.agent_properties)
        else:
            self._refresh_properties({})

    def _refresh_properties(self, existing_values: dict[str, Any]) -> None:
        """Refresh the properties container based on the selected agent type."""
        if self._refreshing:
            return  # Prevent re-entrancy
        
        self._refreshing = True
        try:
            container = self.query_one("#properties-container", Vertical)

            # Clear the dict first to avoid stale references
            self._property_inputs.clear()
            
            # Get the selected agent type's schema first
            select = self.query_one("#agent-type-select", Select)
            agent_type_name = select.value

            if (
                agent_type_name is Select.BLANK
                or not agent_type_name
                or agent_type_name not in self._agent_types
            ):
                # Remove all children if no valid agent type
                for child in list(container.children):
                    child.remove()
                return

            agent_type = self._agent_types[str(agent_type_name)]
            schema = agent_type.property_schema
            properties = schema.get("properties", {})

            # Get IDs of widgets we need to create
            needed_ids = {f"prop-{name}" for name in properties.keys()}
            
            # Remove widgets that are no longer needed or will be replaced
            # Query and remove by ID to ensure they're properly removed
            widgets_to_remove = []
            for prop_id in needed_ids:
                try:
                    widget = container.query_one(f"#{prop_id}", default=None)
                    if widget:
                        widgets_to_remove.append(widget)
                except Exception:
                    pass
            
            # Also remove any other prop- widgets
            for child in list(container.children):
                if hasattr(child, 'id') and child.id and child.id.startswith("prop-"):
                    if child not in widgets_to_remove:
                        widgets_to_remove.append(child)
                elif not hasattr(child, 'id') or not child.id:
                    # Remove Static labels that don't have IDs
                    widgets_to_remove.append(child)
            
            # Remove all widgets
            for widget in widgets_to_remove:
                widget.remove()

            # Mount new widgets immediately - the check in _mount_property_widgets
            # will skip if widgets still exist
            self._mount_property_widgets(container, properties, existing_values)
        except Exception:
            self._refreshing = False
            raise

    def _mount_property_widgets(
        self,
        container: "Vertical",
        properties: dict[str, dict[str, Any]],
        existing_values: dict[str, Any],
    ) -> None:
        """Mount property widgets after removals have completed."""
        try:
            for prop_name, prop_schema in properties.items():
                prop_type = prop_schema.get("type", "string")
                default_value = prop_schema.get("default", "")
                description = prop_schema.get("description", "")

                # Use existing value if present
                value = existing_values.get(prop_name, default_value)

                # Create label
                label_text = prop_name
                if description:
                    label_text = f"{prop_name} ({description})"

                prop_id = f"prop-{prop_name}"
                
                # Check if widget already exists - if so, remove it first
                try:
                    existing_widget = container.query_one(f"#{prop_id}", default=None)
                    if existing_widget:
                        existing_widget.remove()
                        # Schedule mounting this widget after removal
                        self.app.call_later(
                            lambda: self._mount_single_property_widget(
                                container, prop_name, prop_schema, value, prop_id, label_text
                            )
                        )
                        continue
                except Exception:
                    pass  # Widget doesn't exist, proceed
                
                self._mount_single_property_widget(
                    container, prop_name, prop_schema, value, prop_id, label_text
                )
                
        finally:
            self._refreshing = False

    def _mount_single_property_widget(
        self,
        container: "Vertical",
        prop_name: str,
        prop_schema: dict[str, Any],
        value: Any,
        prop_id: str,
        label_text: str,
    ) -> None:
        """Mount a single property widget."""
        try:
            # Check one more time that widget doesn't exist
            existing_widget = container.query_one(f"#{prop_id}", default=None)
            if existing_widget:
                return  # Widget exists, skip
            
            label = Static(f"{label_text}:", classes="form-label")
            container.mount(label)

            prop_type = prop_schema.get("type", "string")
            # Create input based on type
            if prop_type == "integer" or prop_type == "number":
                placeholder = "0-100"
                if "minimum" in prop_schema and "maximum" in prop_schema:
                    placeholder = f"{prop_schema['minimum']}-{prop_schema['maximum']}"
                input_widget = Input(
                    value=str(value) if value else "",
                    placeholder=placeholder,
                    id=prop_id,
                )
            else:
                input_widget = Input(
                    value=str(value) if value else "",
                    id=prop_id,
                )

            container.mount(input_widget)
            self._property_inputs[prop_name] = input_widget
        except Exception:
            pass  # Ignore errors during mounting

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle agent type selection change."""
        if event.select.id == "agent-type-select":
            # Preserve existing property values where possible
            existing_values = self._get_property_values()
            self._refresh_properties(existing_values)

    def _get_property_values(self) -> dict[str, Any]:
        """Get the current property values from inputs."""
        values = {}
        for prop_name, input_widget in self._property_inputs.items():
            value = input_widget.value.strip()
            if value:
                # Try to convert to number if it looks like one
                try:
                    if "." in value:
                        values[prop_name] = float(value)
                    else:
                        values[prop_name] = int(value)
                except ValueError:
                    values[prop_name] = value
        return values

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-save-agent":
            self._save_agent_config()

    def _save_agent_config(self) -> None:
        """Save the current agent configuration."""
        if not self.state.selected_character:
            self.notify("No character selected", severity="error")
            return

        from models import CharacterAgentConfig, CharacterProfile

        profile = self.state.profiles.get(self.state.selected_character)
        if not profile:
            self.notify("Character not found", severity="error")
            return

        agent_type_value = self.query_one("#agent-type-select", Select).value
        agent_type = (
            str(agent_type_value)
            if agent_type_value is not Select.BLANK and agent_type_value
            else "default"
        )
        instructions = self.query_one("#agent-instructions", TextArea).text.strip()
        properties = self._get_property_values()

        agent_config = CharacterAgentConfig(
            agent_type=agent_type,
            agent_properties=properties,
            agent_instructions=instructions,
        )

        # Update the profile with new agent config
        updated_profile = CharacterProfile(
            name=profile.name,
            description=profile.description,
            role=profile.role,
            motivations=profile.motivations,
            relationships=profile.relationships,
            backstory=profile.backstory,
            agent_config=agent_config,
        )

        self.state.update_profile(profile.name, updated_profile)
        self.notify(f"Saved agent config for: {profile.name}")

        # Refresh the character list in the parent screen
        from tui.widgets.character_list import CharacterListPane

        try:
            list_pane = self.screen.query_one(CharacterListPane)
            list_pane.refresh_list()
        except Exception:
            pass  # List pane might not be mounted yet
