# Setup Guide

Full walkthrough from a fresh Home Assistant install to a working
Approve / Decline notification on your phone.

---

## Prerequisites

| Requirement | Why |
|---|---|
| Seerr (Overseerr / Jellyseerr) reachable from Home Assistant | Source of the requests and target of the approve/decline calls |
| Official **Seerr** integration (`overseerr`) | Registers the webhook and creates `event.overseerr_last_media_event` |
| **CSRF Protection disabled** in Seerr | The integration cannot register its webhook while CSRF protection is on |
| Home Assistant Companion app (Android or iOS) | Actionable notifications with image and buttons |
| Home Assistant 2024.12 or newer | `overseerr` integration and the `triggers:` / `actions:` automation syntax |

---

## Step 1: Add the Seerr integration

1. Go to **Settings** -> **Devices & Services** -> **Add Integration**.
2. Search for **Seerr**.
3. Enter the server URL (e.g. `http://192.168.1.10:5055`) and the API key.
4. Submit.

Getting the API key: **Seerr** -> **Settings** -> **General** -> **API Key**.

> The integration creates and maintains the webhook inside Seerr on its own and
> rewrites it on every reload. **Do not edit that webhook by hand** - your
> changes will be overwritten on the next restart.

### What the integration can and cannot do

The official integration exposes exactly three actions:

- `overseerr.get_requests`
- `overseerr.request_media`
- `overseerr.search_media`

**Approving and declining is not among them.** Older guides from the
`vaparr/ha-overseerr` wiki use `overseerr.update_request`, which was a service
of a custom component and no longer exists.

That is the whole reason this repository exists: the integration handles the
push side (webhook events), and the decision side goes through `rest_command`
straight to the Seerr API:

```
POST /api/v1/request/{id}/approve
POST /api/v1/request/{id}/decline
```

---

## Step 2: Store the API key in secrets.yaml

Add to `config/secrets.yaml`:

```yaml
seerr_api_key: YOUR_API_KEY_HERE
```

Keeping the key out of `configuration.yaml` matters: anything in the main
config ends up in every backup and in the integration diagnostics download.

---

## Step 3: Add the REST commands

Copy [`examples/rest_commands.yaml`](../examples/rest_commands.yaml) to
`config/rest_commands.yaml`, replace `IP_SEERR`, and include it from
`configuration.yaml`:

```yaml
rest_command: !include rest_commands.yaml
```

Three rules that cost hours if broken - see
[Troubleshooting](troubleshooting.md) for the failure modes:

1. The included file must **not** repeat the `rest_command:` key, and command
   names live in column 0.
2. Command names are slugs: **no capital letters**.
3. `rest_command` is only read at boot. **Restart** Home Assistant - "Reload
   YAML configuration" is not enough.

> Prefer a single file? [`packages/seerrha.yaml`](../packages/seerrha.yaml)
> contains the REST commands and the automation in one package.

---

## Step 4: Import the blueprint

[![Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint=https%3A%2F%2Fgithub.com%2Fvednolacni%2FSeerrHA%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fseerrha%2Fseerr_request_approval.yaml)

Or manually: **Settings** -> **Automations & Scenes** -> **Blueprints** ->
**Import Blueprint**, and paste:

```
https://github.com/vednolacni/SeerrHA/blob/main/blueprints/automation/seerrha/seerr_request_approval.yaml
```

Then **Create Automation** from the blueprint and fill in:

| Input | Value |
|---|---|
| Seerr event entity | `event.overseerr_last_media_event` |
| REST command | `rest_command.seerrha_request_action` |
| Notify service | your own, e.g. `notify.mobile_app_pixel_9` - `your_phone` is a placeholder |

### Finding your notify service

**Developer Tools** -> **Actions** -> search `notify.mobile_app`. Pick the one
matching your device.

> A notify **entity** (`notify.your_phone`) is not the same thing. Entities
> only support `send_message` - no image, no action buttons. You need the
> `notify.mobile_app_*` **action**.

---

## Step 5: Verify

### Is the API key valid?

**Developer Tools** -> **Actions** -> **YAML mode**:

```yaml
action: rest_command.seerrha_test
data: {}
```

A `404` with `Request not found.` is a **good** result here - it means
authentication succeeded and only that specific request ID is missing. See the
[response table](troubleshooting.md#telling-api-responses-apart).

### Does approving work?

```yaml
action: rest_command.seerrha_request_action
data:
  request_id: 35
  cmd: approve
```

Get real IDs of pending requests from **Developer Tools** -> **Actions** ->
**Seerr: Get requests** with status `pending`.

### Does the phone send responses back?

**Developer Tools** -> **Events** -> listen to `mobile_app_notification_action`
and press a button on the notification. You should see an event with
`action: SEERR_APPROVE_35`.

---

## Step 6: End-to-end test

Submit a request in Seerr from a non-admin account (an admin's own requests are
auto-approved and arrive as `auto_approved`, not `pending`). The notification
should arrive within seconds with the poster, the requester's name and both
buttons.
