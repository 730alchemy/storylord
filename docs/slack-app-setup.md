# Running the Slack Character Creation App

The Slack app lets users interactively define characters via a `/create-character`
slash command. Saved characters are persisted to the local character library and
can be referenced in Storylord story inputs via the `character_library` field.

## How it connects

The app supports two connection modes, selected at runtime based on which tokens
are present in the environment:

- **Socket Mode** (recommended) — the app connects outbound to Slack via
  WebSocket. No public URL is needed. Works on localhost. The Slack client can be
  on any device — phone, desktop, browser — on any network.
- **HTTP mode** — the app runs an HTTP server and Slack POSTs events/commands to
  it. Requires a publicly reachable HTTPS URL (ngrok, cloud deploy, etc.).

If `SLACK_APP_TOKEN` is set, Socket Mode is used. Otherwise the app falls back to
HTTP mode on port 3000.

## Prerequisites

A Slack workspace and a Slack app configured at <https://api.slack.com/apps>.

### 1. Create the Slack app

Go to <https://api.slack.com/apps> → **Create an app** → **From scratch**.
Select your workspace.

### 2. Configure the slash command

**Slash Commands** → **Add New Command**

| Field | Value |
|-------|-------|
| Command | `/create-character` |
| Request URL | _(leave blank if using Socket Mode)_ |
| Short description | Create a character for Storylord |

### 3. Subscribe to events

Slash commands arrive without event subscriptions, but the DM conversation
flow requires them.

**Event Subscriptions** → toggle **on** → under **Bot Events** click
**Add Bot Event** and add:

| Event |
|-------|
| `message:im` |

Save.

> **Note:** In Socket Mode the Request URL field can be left blank.

### 4. Install the app

The app needs two scopes:

- `commands` — auto-granted for slash commands.
- `chat:write` — required to send DM replies during the character creation
  conversation.

Add `chat:write` under **OAuth & Permissions** → **Scopes** → **Bot Token Scopes**
before installing (or reinstalling).

Install the app to your workspace. Copy the **Bot User OAuth Token** (`xoxb-...`)
from the **Install App** page — you will need it in step 6.

> **Note:** If you previously installed the app without `chat:write`, add the scope
> and reinstall. Reinstallation is required for new scopes to take effect.

### 5. Enable Socket Mode and generate an app-level token

**Settings** → check **Use Socket Mode**.

**Install App** → scroll to **App-Level Tokens** → **Generate Token**.
Select the `connections:open` scope. Copy the generated token (`xapp-...`).

### 6. Copy tokens into `.env`

Add these three values to the project `.env` file:

```
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
SLACK_APP_TOKEN=xapp-...
```

- `SLACK_BOT_TOKEN` — from Install App → Installed App Settings (step 4)
- `SLACK_SIGNING_SECRET` — from Settings → Basic Information
- `SLACK_APP_TOKEN` — the app-level token generated in step 5

## Running

```
pdm run slack
```

The app connects to Slack and `/create-character` becomes available in any
channel in your workspace.

## Switching to HTTP mode

Remove `SLACK_APP_TOKEN` from `.env`. The app will start an HTTP server on
port 3000 instead. You will need to provide a publicly reachable HTTPS URL
(e.g. via ngrok) and set it as the **Request URL** for the `/create-character`
slash command in the Slack app config.
