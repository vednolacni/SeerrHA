# Setup Guide

Full walkthrough from a fresh Home Assistant install to a working
Approve / Decline notification on your phone.

---

## Prerequisites

| Requirement | Why |
|---|---|
| Seerr (Overseerr / Jellyseerr) reachable from Home Assistant | Source of the requests and target of the approve/decline calls |
| Official **[Seerr integration](https://www.home-assistant.io/integrations/overseerr/)** (`overseerr`) | Registers the webhook and creates `event.overseerr_last_media_event` |
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

## Step 2: Get the API key

**Seerr** -> **Settings** -> **General** -> **API Key**. Keep it to hand - you
paste it into the blueprint in step 4. Nothing to configure here.

> **Where the key ends up.** Blueprint inputs are stored in plain text in
> `automations.yaml` and show up in automation traces, so the key travels into
> backups and diagnostics downloads. That is the trade for not hand-editing
> YAML.
>
> To keep it out of there, set the `X-Api-Key` header in your
> `rest_commands.yaml` to `!secret seerr_api_key`, add
> `seerr_api_key: YOUR_KEY` to `config/secrets.yaml`, and leave the blueprint's
> API key field blank. The command then reads the secret and ignores what the
> blueprint passes.

---

## Step 3: Add the REST commands

Copy [`examples/rest_commands.yaml`](../examples/rest_commands.yaml) to
`config/rest_commands.yaml` **unchanged** - the URL and the key are passed in
by the blueprint - and include it from `configuration.yaml`:

```yaml
rest_command: !include rest_commands.yaml
```

Three rules that cost hours if broken - see
[Troubleshooting](troubleshooting.md) for the failure modes:

1. The included file must **not** repeat the `rest_command:` key, and command
   names live in column 0.
2. Command names are slugs: **no capital letters**.
3. **Restart** Home Assistant this first time. `rest_command` is not loaded
   until the key exists in your configuration, so there is nothing to reload
   yet. From then on `rest_command.reload` is enough for new or renamed
   commands - note that *Reload core configuration* is **not** the same thing
   and will not pick them up.

> Prefer a single file? [`packages/seerrha.yaml`](../packages/seerrha.yaml)
> contains the REST commands and the automation in one package.

---

## Step 4: Import the blueprint

[![Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fvednolacni%2FSeerrHA%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fseerrha%2Fseerr_request_approval.yaml)

Or manually: **Settings** -> **Automations & Scenes** -> **Blueprints** ->
**Import Blueprint**, and paste:

```
https://github.com/vednolacni/SeerrHA/blob/main/blueprints/automation/seerrha/seerr_request_approval.yaml
```

Then **Create Automation** from the blueprint and fill in:

| Input | Value |
|---|---|
| Seerr event entity | `event.overseerr_last_media_event` |
| Seerr URL | e.g. `http://192.168.1.10:5055` - no trailing slash |
| Seerr API key | from step 2, or blank if you went the `!secret` route |
| Phone | pick your device from the list |

### Phone, or notify service?

**Phone** is a device picker listing only devices that run the Companion app,
so there is nothing to type and nothing to get wrong. Use it unless you need
something it cannot express.

**Notify service (advanced)** overrides it, and is there for one case: a
notification **group** covering several phones, e.g. `notify.all_phones`. Find
service names under **Developer Tools** -> **Actions** -> `notify.mobile_app`.

> If you use the advanced field, a notify **entity** (`notify.your_phone`) is
> not the same thing. Entities only support `send_message` - no image, no action
> buttons. You need the `notify.mobile_app_*` **action**.

> The blueprint derives the service from the device's *registered* name. If you
> renamed the phone inside the Companion app and notifications stop arriving,
> put the real service name in the advanced field.

---

## Step 5: Verify

### Is the API key valid?

**Developer Tools** -> **Actions** -> **YAML mode**:

```yaml
action: rest_command.seerrha_test
data:
  base_url: "http://192.168.1.10:5055"
  api_key: "YOUR_API_KEY"
```

This reads one request and changes nothing. A `200` means the key works. A
`403` means the key is wrong or CSRF protection is still on - see the
[response table](troubleshooting.md#telling-api-responses-apart).

### Does approving work?

```yaml
action: rest_command.seerrha_request_action
data:
  base_url: "http://192.168.1.10:5055"
  api_key: "YOUR_API_KEY"
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
