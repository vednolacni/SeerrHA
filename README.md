# SeerrHA

[![Home Assistant][ha-badge]][ha-url]
[![Blueprint][blueprint-badge]][blueprint-url]
[![License][license-badge]](LICENSE)

Approve or decline Seerr requests straight from a mobile notification.

A push notification arrives on your phone the moment someone requests something
in Seerr - with the poster, the requester's name and **Approve** / **Decline**
buttons. Pressing a button sends the decision back to Seerr.

Built for: Seerr (Overseerr / Jellyseerr) + Jellyfin + Radarr/Sonarr, Home
Assistant with the official **Seerr** (`overseerr`) integration and the
Companion app.

## Features

- 📲 **Actionable push notifications**: poster art, title, requester and season list in one notification
- ✅ **Approve / Decline from the lock screen**: the decision is POSTed straight to the Seerr API
- 🧩 **Importable blueprint**: notify service, button labels and extras configured in the UI
- 📦 **One-file package**: `packages/seerrha.yaml` carries the REST commands and the automation together
- 🖼️ **No TMDB lookups**: the poster URL already arrives in `entity_picture`
- 📺 **TV-aware**: requested seasons are pulled out of the `extra` list and shown in the message
- 🔔 **Auto-dismiss**: the notification clears itself on both devices once a decision is made
- 🎬 **Optional "ready to watch" alert**: a second notification when the request flips to `available`
- 🗒️ **Optional daily digest**: reminder listing requests still waiting for a decision
- 🧵 **`mode: queued`**: several requests at once, none dropped
- 🔐 **API key in `secrets.yaml`**: stays out of backups and diagnostics
- 🤖 **[`llms.txt`](llms.txt)**: compact spec so ChatGPT/Claude/Cursor stop inventing `overseerr.update_request`

## Why the integration alone is not enough

The official Seerr integration exposes exactly three actions:

- `overseerr.get_requests`
- `overseerr.request_media`
- `overseerr.search_media`

**Approving and declining is not among them.** Older guides from the
`vaparr/ha-overseerr` wiki use `overseerr.update_request` - that was a service of
a custom component and no longer exists.

So the work is split: the integration handles the push side (webhook events),
and the decisions go through `rest_command` directly to the Seerr API:

```
POST /api/v1/request/{id}/approve
POST /api/v1/request/{id}/decline
```

## Documentation

| Guide | Description |
|---|---|
| **[Setup Guide](docs/setup.md)** | Step-by-step from integration to a working notification, including verification actions |
| **[Event & Data Reference](docs/event-reference.md)** | Attribute structure of `event.overseerr_last_media_event`, event types, API endpoints, action-name format |
| **[Troubleshooting & FAQ](docs/troubleshooting.md)** | Slug errors, stale REST commands, 403 hunts, notify entity vs. action, statuses stuck on "Requested" |
| **[Examples & Cookbook](examples/README.md)** | Ready-to-use automations, scripts and dashboard cards |
| **[AI Assistant Context (`llms.txt`)](llms.txt)** | Compact, authoritative reference designed for prompt context |

## Requirements

| Requirement | Why |
|---|---|
| Home Assistant 2024.12+ | `overseerr` integration and the `triggers:` / `actions:` automation syntax |
| Official **Seerr** integration | Registers the webhook and creates `event.overseerr_last_media_event` |
| **CSRF Protection disabled** in Seerr | The integration cannot register its webhook while CSRF protection is on |
| Seerr API key | Seerr -> Settings -> General -> API Key |
| Companion app (Android / iOS) | Notifications with images and action buttons |

## Installation

SeerrHA needs two pieces: the REST commands (outbound) and the automation
(inbound). Pick **either** the blueprint route or the package route.

### Step 1: Add the Seerr integration

1. **Settings** -> **Devices & Services** -> **Add Integration**.
2. Search for **Seerr**.
3. Enter the server URL (e.g. `http://192.168.1.10:5055`) and the API key.

> The integration creates the webhook inside Seerr itself and overwrites it on
> every reload - **do not edit that webhook by hand**.

### Step 2: Store the API key

`config/secrets.yaml`:

```yaml
seerr_api_key: YOUR_API_KEY_HERE
```

### Step 3: Add the REST commands

Copy [`examples/rest_commands.yaml`](examples/rest_commands.yaml) to
`config/rest_commands.yaml`, replace `IP_SEERR`, and include it:

```yaml
# configuration.yaml
rest_command: !include rest_commands.yaml
```

Then **restart Home Assistant**. `rest_command` is only read at boot - "Reload
YAML configuration" will not pick up a new command.

> The included file must not repeat the `rest_command:` key, and command names
> must be lowercase slugs. Both mistakes have loud, misleading failure modes -
> see [Troubleshooting](docs/troubleshooting.md#rest-command-issues).

### Step 4: Import the blueprint

[![Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled.][import-badge]][import-url]

Or **Settings** -> **Automations & Scenes** -> **Blueprints** -> **Import
Blueprint**, and paste:

```
https://github.com/vednolacni/SeerrHA/blob/main/blueprints/automation/seerrha/seerr_request_approval.yaml
```

Create an automation from it and fill in your notify service
(`notify.mobile_app_<your_phone>`).

### Alternative: the package route

Skip steps 3 and 4 and drop [`packages/seerrha.yaml`](packages/seerrha.yaml)
into `config/packages/` instead:

```yaml
# configuration.yaml
homeassistant:
  packages: !include_dir_named packages
```

Edit `IP_SEERR` and the notify service inside the file, then restart.

## Blueprint Options

| Input | Default | Description |
|---|---|---|
| **Seerr event entity** | `event.overseerr_last_media_event` | The event entity created by the integration |
| **REST command** | `rest_command.seerrha_request_action` | Command that performs the approve/decline call |
| **Notify service** | - | The Companion **action**, e.g. `notify.mobile_app_matic_s_phone` |
| **Approve / Decline labels** | `Approve` / `Decline` | Button text |
| **Notification channel** | `Seerr` | Android channel for grouping and per-channel sounds |
| **Sticky notification** | `true` | Keep the notification until a button is pressed (Android) |
| **Confirmation notification** | `true` | Short follow-up confirming the POST went through |
| **Notify when available** | `false` | Extra notification once the content is ready to watch |

> **Notify service, not notify entity.** `notify.matic_s_phone` (entity) supports
> only `send_message` - no images, no buttons. You need the
> `notify.mobile_app_*` action.

## Verifying the setup

```yaml
# 1. Is the key valid? (GET, changes nothing)
action: rest_command.seerrha_test
data: {}

# 2. Does approving work?
action: rest_command.seerrha_request_action
data:
  request_id: 35
  cmd: approve
```

For IDs of pending requests: **Developer Tools** -> **Actions** -> **Seerr: Get
requests**, status `pending`.

To check whether the phone sends responses at all: **Developer Tools** ->
**Events** -> listen to `mobile_app_notification_action` and press a button.

| Response | Meaning |
|---|---|
| `404` + `path: /api/v1/request//` | Empty `request_id` (you sent `data: {}`) |
| `404` + `Request not found.` | **The key is valid**, that request ID does not exist |
| `403` + `You do not have permission` | Invalid API key |
| `200` | Success |

The second `404` is a good sign: authentication succeeded.

## Design Decisions

**The request ID lives in the action name** (`SEERR_APPROVE_35`), not in `tag`.
The Companion app does not reliably forward the `tag` field in the
`mobile_app_notification_action` event on both platforms; the action name always
comes through. Parsed with `split('_')[2]`.

**One automation with `choose`**, not two. Both triggers share a context, so the
notify service is defined once.

**`mode: queued` is mandatory** - with several requests arriving at once, none
is dropped.

**Data comes from `trigger.to_state`**, never from `state_attr()`. The entity can
already be overwritten by the next event while the automation is still running.

**Never store the whole attribute dictionary in a variable.** It contains
`EventEntityStateAttribute.*` enum keys, so Home Assistant renders it as a
string and every later `.request` access raises `UndefinedError`. Store concrete
fields instead.

## Support

- [Report an issue](https://github.com/vednolacni/SeerrHA/issues)
- [Seerr integration - Home Assistant docs](https://www.home-assistant.io/integrations/overseerr/)
- [`rest_command` - Home Assistant docs](https://www.home-assistant.io/integrations/rest_command)
- [Overseerr webhook payload](https://docs.overseerr.dev/using-overseerr/notifications/webhooks)

## Acknowledgments

README structure and documentation layout inspired by
[JellyHA](https://github.com/zupancicmarko/jellyha).

This project was developed with the assistance of AI.

## License

MIT

## Disclaimer

**Personal Use Only**
SeerrHA is configuration glue between your own Home Assistant instance and your
own Seerr server. It does not provide, facilitate or encourage the use of
unauthorized or pirated content. You are solely responsible for the legality of
the media you host and stream.

[ha-badge]: https://img.shields.io/badge/Home%20Assistant-2024.12%2B-41BDF5.svg
[ha-url]: https://www.home-assistant.io/integrations/overseerr/
[blueprint-badge]: https://img.shields.io/badge/Blueprint-Automation-03a9f4.svg
[blueprint-url]: blueprints/automation/seerrha/seerr_request_approval.yaml
[license-badge]: https://img.shields.io/badge/License-MIT-green.svg
[import-badge]: https://my.home-assistant.io/badges/blueprint_import.svg
[import-url]: https://my.home-assistant.io/redirect/blueprint_import/?blueprint=https%3A%2F%2Fgithub.com%2Fvednolacni%2FSeerrHA%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fseerrha%2Fseerr_request_approval.yaml
