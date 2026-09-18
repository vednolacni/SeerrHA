# SeerrHA Examples & Cookbook

Copy-paste ready automations and a helper script for approving and declining
Seerr requests from Home Assistant.

> **Prompting an AI assistant (ChatGPT, Claude, Cursor)?**
> Feed [**`llms.txt`**](../llms.txt) into your prompt to get accurate,
> hallucination-free automations for this setup - including the nested attribute
> structure that trips up most generated templates.

---

## Automations

| Recipe | Description | Trigger |
|:---|:---|:---|
| **[Request approval](automations/seerr_request_approval.yaml)** | Actionable notification with poster, requester and Approve/Decline buttons, plus the handler that POSTs the decision back to Seerr. | State (`event.overseerr_last_media_event`) + `mobile_app_notification_action` |
| **[Media available notification](automations/seerr_available_notification.yaml)** | Notifies with poster art once a request flips to `available`. | State (`event_type == 'available'`) |
| **[Pending requests reminder](automations/seerr_pending_reminder.yaml)** | Daily summary of requests still waiting for a decision, via `overseerr.get_requests` - no API key needed. | Time |

The approval recipe is also available as an importable
[**blueprint**](../blueprints/automation/seerrha/seerr_request_approval.yaml)
with UI inputs for the notify service, button labels and optional extras. The
blueprint also covers the "media available" recipe as an option, so those two
standalone files are only needed on the package route.

---

## Scripts

| Script | Description | Invocation |
|:---|:---|:---|
| **[Decide request by ID](scripts/seerr_decide_request.yaml)** | Approves or declines a request by its numeric ID and reports the HTTP status back as a persistent notification. | Action call / voice / Developer Tools |

---

## Configuration files

| File | Description |
|:---|:---|
| **[`rest_commands.yaml`](rest_commands.yaml)** | The `approve` / `decline` REST commands plus a read-only smoke test, ready for `rest_command: !include rest_commands.yaml`. |
| **[`packages/seerrha.yaml`](../packages/seerrha.yaml)** | Everything in one package file: REST commands and the automation. |

---

## How to use these examples

### Adding an automation

1. **Settings** -> **Automations & Scenes** -> **Automations**.
2. **Create Automation** -> **Create new automation**.
3. Three-dot menu (**⋮**) -> **Edit in YAML**.
4. Paste the contents of a file from [`automations/`](automations/).
5. Replace `notify.mobile_app_your_phone` with your own notify action and save.

### Adding a script

1. **Settings** -> **Automations & Scenes** -> **Scripts** -> **Add Script**.
2. **⋮** -> **Edit in YAML** and paste a file from [`scripts/`](scripts/).

### Adding the REST commands

See [Setup step 3](../docs/setup.md#step-3-add-the-rest-commands). Remember that
`rest_command` requires a **restart**, not just a YAML reload.

---

## Not included: dashboard cards

A dashboard card with Approve / Decline buttons looks obvious but does not work
with the built-in cards: Lovelace does not render Jinja templates in card
configuration (only the Markdown card does), so a `tap_action` cannot look up
the current request ID. The buttons would send the template as a literal string.

Approve and decline from the notification, or call
[`script.seerrha_decide_request`](scripts/seerr_decide_request.yaml) with an ID
you already know.
