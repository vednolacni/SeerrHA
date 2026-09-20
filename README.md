<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/logo-wide-dark.png">
  <img src="docs/images/logo-wide.png" alt="SeerrHA" width="440">
</picture>

### Approve or decline Seerr requests straight from a mobile notification.

[![Home Assistant][ha-badge]][ha-url]
[![Blueprint][blueprint-badge]][blueprint-url]
[![License][license-badge]](LICENSE)

Built for Home Assistant with the official **Seerr** (`overseerr`) integration.<br>
Not a custom component - plain configuration that adds the one action the integration is missing.

[Setup](docs/setup.md) &middot; [Examples](examples/README.md) &middot; [Troubleshooting](docs/troubleshooting.md) &middot; [Event reference](docs/event-reference.md)

<img src="docs/images/notification-request.webp" alt="A new request on the lock screen, with poster art and Approve and Decline buttons" width="300">
<img src="docs/images/notification-result.webp" alt="Confirmation notification once the decision reaches Seerr" width="300">

</div>

---

A push notification arrives on your phone the moment someone requests something
in Seerr - with the poster, the requester's name and **Approve** / **Decline**
buttons. Pressing a button sends the decision back to Seerr.

SeerrHA is not a custom component and not a replacement for the official
integration - it is plain Home Assistant configuration that adds the one thing
the integration does not have: **approving and declining requests**. The
integration ships only `get_requests`, `request_media` and `search_media`, so
the decision goes out through `rest_command` straight to the Seerr REST API.

> Older guides reach for `overseerr.update_request`. That was a service of the
> `vaparr/ha-overseerr` custom component, not of the official integration, and
> it no longer exists. The [Setup Guide](docs/setup.md) has the details.

## Features

- 📲 **Actionable push notifications**: poster art, title, requester and season list in one notification
- ✅ **Approve / Decline from the lock screen**: the decision is POSTed straight to the Seerr API
- 🧩 **Importable blueprint**: notify service, button labels and extras configured in the UI
- 📦 **One-file package**: `packages/seerrha.yaml` carries the REST commands and the automation together
- 🖼️ **No TMDB lookups**: the poster URL already arrives in `entity_picture`
- 📺 **TV-aware**: requested seasons are pulled out of the `extra` list and shown in the message
- 🔔 **Auto-dismiss**: the notification clears itself on both devices once a decision is made
- 🧵 **`mode: queued`**: several requests at once, none dropped
- 🔐 **No file editing**: the Seerr URL and API key are blueprint inputs, not hand-edited YAML
- 🤖 **[`llms.txt`](llms.txt)**: compact spec so ChatGPT/Claude/Cursor stop inventing `overseerr.update_request`

## Requirements

| Requirement | Why |
|---|---|
| Home Assistant 2024.12+ | `overseerr` integration and the `triggers:` / `actions:` automation syntax |
| Official **[Seerr integration](https://www.home-assistant.io/integrations/overseerr/)** | Registers the webhook and creates `event.overseerr_last_media_event` |
| **CSRF Protection disabled** in Seerr | The integration cannot register its webhook while CSRF protection is on |
| Seerr API key | Seerr -> Settings -> General -> API Key |
| Companion app (Android / iOS) | Notifications with images and action buttons |

## Installation

SeerrHA needs two pieces: the REST commands (outbound) and the automation
(inbound). Pick **either** the blueprint route or the package route - the
[Setup Guide](docs/setup.md) walks through both in detail.

1. **Add the Seerr integration** - Settings -> Devices & Services -> Add
   Integration -> **Seerr**, with your server URL and API key.
2. **Add the REST commands** - copy
   [`examples/rest_commands.yaml`](examples/rest_commands.yaml) as-is (nothing
   to edit), include it with `rest_command: !include rest_commands.yaml`, then
   **restart** Home Assistant.
3. **Import the blueprint** and fill in your Seerr URL, API key and notify
   service.

[![Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled.][import-badge]][import-url]

> Prefer one file? Skip steps 2 and 3 and drop
> [`packages/seerrha.yaml`](packages/seerrha.yaml) into `config/packages/`
> instead, then edit the three values at the top of its `variables:` block.

Two mistakes cost hours, so they are worth repeating: command names must be
lowercase slugs, and that first restart is genuinely required - `rest_command`
is not loaded until the key exists, so there is nothing to reload yet. Later
edits only need `rest_command.reload`. Both fail in misleading ways - see
[Troubleshooting](docs/troubleshooting.md#rest-command-issues).

### Placeholders you must replace

Nothing in this repository works until these are swapped for your own values.
None of them are real.

On the blueprint route you fill these into the UI and edit no files at all. The
package and the standalone examples carry them as placeholders instead.

| Placeholder | Replace with | Where to find it |
|---|---|---|
| `notify.mobile_app_your_phone` | Your Companion **action**, e.g. `notify.mobile_app_pixel_9` | **Developer Tools** -> **Actions**, search `notify.mobile_app` and pick your device |
| `IP_SEERR` | Host or IP of your Seerr server | The address you open Seerr on (port `5055` by default) |
| `YOUR_SEERR_API_KEY` | Your Seerr API key | **Seerr** -> **Settings** -> **General** -> **API Key** |
| `YOUR_CONFIG_ENTRY_ID` | The Seerr integration's config entry ID (only the pending-requests reminder needs it) | Build the action once in **Developer Tools** -> **Actions** -> **Seerr: Get requests**, then switch to YAML mode and copy it |

`event.overseerr_last_media_event` is **not** a placeholder - the integration
creates that entity with exactly that name.

## Blueprint Options

| Input | Default | Description |
|---|---|---|
| **Seerr event entity** | `event.overseerr_last_media_event` | The event entity created by the integration |
| **Seerr URL** | - | e.g. `http://192.168.1.10:5055`, no trailing slash |
| **Seerr API key** | - | Seerr -> Settings -> General -> API Key. See the note below |
| **Phone** | - | Device picker, listing only phones running the Companion app |
| **Notify service (advanced)** | - | Leave empty unless you need a notification group covering several phones |
| **Approve / Decline labels** | `Approve` / `Decline` | Button text |
| **Notification channel** | `Seerr` | Android channel for grouping and per-channel sounds |
| **Sticky notification** | `true` | Keep the notification until a button is pressed (Android) |
| **Confirmation notification** | `true` | Short follow-up confirming the POST went through |
| **Notify when available** | `false` | Extra notification once the content is ready to watch |
| **Action prefix** | `SEERR` | Only change it if you build a *second* automation from this blueprint - see below |

> **One automation, not one per phone.** The button press arrives as an event
> with no device information, so every automation built from this blueprint
> reacts to every press - two of them would send the decision to Seerr twice.
> Put a notification **group** covering all your phones in **Notify service
> (advanced)**, or give each automation its own **Action prefix**.

If the POST fails, the notification is **not** cleared and you get an error with
the HTTP status instead, because the request is still sitting in Seerr
undecided.

> **Where the API key lives.** Blueprint inputs are stored in plain text in
> `automations.yaml` and appear in automation traces, so the key reaches backups
> and diagnostics downloads. To keep it in `secrets.yaml` instead, set the
> `X-Api-Key` header in your `rest_commands.yaml` to `!secret seerr_api_key` and
> leave the blueprint field blank - the command reads the secret and ignores
> what the blueprint passes.

> **If you use the advanced field: service, not entity.** `notify.your_phone`
> (entity) supports only `send_message` - no images, no buttons. You need the
> `notify.mobile_app_*` action. The **Phone** picker always resolves to the
> right one, so prefer it.

## Documentation

| Guide | Description |
|---|---|
| **[Setup Guide](docs/setup.md)** | Step-by-step from integration to a working notification, including the verification actions |
| **[Event & Data Reference](docs/event-reference.md)** | Attribute structure of `event.overseerr_last_media_event`, event types, API endpoints, action-name format and the design decisions behind them |
| **[Troubleshooting & FAQ](docs/troubleshooting.md)** | Slug errors, stale REST commands, 403 hunts, notify entity vs. action |
| **[Examples & Cookbook](examples/README.md)** | Ready-to-use automations and a helper script |
| **[AI Assistant Context (`llms.txt`)](llms.txt)** | Compact, authoritative reference designed for prompt context |

## Support

- [Report an issue](https://github.com/vednolacni/SeerrHA/issues)
- [Seerr integration - Home Assistant docs](https://www.home-assistant.io/integrations/overseerr/)
- [`rest_command` - Home Assistant docs](https://www.home-assistant.io/integrations/rest_command)
- [Overseerr webhook payload](https://docs.overseerr.dev/using-overseerr/notifications/webhooks)

## Credits

SeerrHA started from [**vaparr/ha-overseerr**](https://github.com/vaparr/ha-overseerr)
and its *Phone Notifications in Home Assistant* wiki page, which was the first
public recipe for approving Overseerr requests from a Companion notification.
That project is a HACS custom component; its `overseerr.update_request` service
and `sensor.overseerr_pending_requests` no longer apply now that Home Assistant
ships an official `overseerr` integration under the same domain.

SeerrHA is the same idea rebuilt on the official integration, with three changes
that came out of running it:

- **decisions go to the REST API**, because the official integration has no
  approve/decline action to call;
- **the request ID travels in the action name** (`SEERR_APPROVE_35`) instead of
  in `tag`, which the Companion app does not forward reliably on both platforms;
- **action names are prefixed**, so they no longer collide with bare `approve` /
  `deny` actions coming from other notifications.

README structure and documentation layout inspired by
[**JellyHA**](https://github.com/zupancicmarko/jellyha) - and if you run
Jellyfin, go and look at it properly. It is a seriously good integration with a
far wider scope than this repository has: SeerrHA does one thing, JellyHA does
the whole media-server side.

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
[import-url]: https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fvednolacni%2FSeerrHA%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fseerrha%2Fseerr_request_approval.yaml
