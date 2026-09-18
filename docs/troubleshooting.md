# Troubleshooting & FAQ

Every entry below is a failure that actually happened while building this setup.

---

## REST command issues

### `Invalid config for 'rest_command': invalid slug`

```
Invalid config for 'rest_command': invalid slug seerrHA_request_action
(try seerrha_request_action)
```

Command names are slugs - lowercase letters, digits and underscores only.

The nasty part: on this error the **entire** `rest_command` block fails to load,
but the definitions from the previous boot **stay in memory**. Calls appear to
work while silently using stale data (for example an API key you already
rotated). This was the source of a very long hunt for a `403`.

After fixing the name, restart Home Assistant and re-run the smoke test.

---

### `'seerrha_request_action' is an invalid option for 'rest_command'`

```
'seerrha_request_action' is an invalid option for 'rest_command',
check: rest_command->pipup_url_on_tv->seerrha_request_action
```

Indentation. Two spaces too many turned the command into a sub-option of the
previous command. In an `!include`d file, command names belong in column 0 and
the file must **not** repeat the `rest_command:` key.

---

### A new REST command does not exist after "Reload YAML"

`rest_command` is only evaluated at startup. A new or renamed command requires a
full **restart** of Home Assistant.

Automations are the opposite - they refresh as soon as you save them.

---

## Notification issues

### No image and no buttons on the notification

You are calling a notify **entity** instead of a notify **action**.

- `notify.matic_s_phone` (entity) - supports only `send_message`. No image, no
  actions.
- `notify.mobile_app_matic_s_phone` (action) - full Companion payload.

Find the right one under **Developer Tools** -> **Actions** ->
`notify.mobile_app`.

---

### Buttons do nothing

Listen to the event first: **Developer Tools** -> **Events** -> listen to
`mobile_app_notification_action`, then press a button.

- **No event at all** - the phone is not delivering the response. Check that the
  Companion app has notification permissions and that the device is registered
  under **Settings** -> **Devices & Services** -> **Mobile App**.
- **Event arrives, nothing happens** - check the automation trace. The most
  common cause is the `SEERR_` prefix not matching (the condition uses
  `startswith('SEERR_')`) or the REST command failing.

---

### The notification disappears before I can decide

Set `sticky: true` in the notification data (Android). Without it a swipe
dismisses it and the request stays pending.

---

## Template issues

### `UndefinedError: 'str object' has no attribute 'request'`

```yaml
# DOES NOT WORK
a: "{{ trigger.to_state.attributes }}"
```

The attribute dictionary contains enum keys
(`EventEntityStateAttribute.EVENT_TYPE`), so Home Assistant cannot convert it
back into a dict and it stays a string.

**Always store concrete fields**, never the whole dictionary:

```yaml
# WORKS
rid: "{{ trigger.to_state.attributes['request']['request_id'] }}"
```

---

### Values belong to the previous request

Read from `trigger.to_state`, not from `state_attr()`. With several requests
arriving close together the entity can already hold the next event by the time
your action runs. `mode: queued` keeps the runs in order, but only
`trigger.to_state` keeps each run's data.

---

## API issues

### Telling API responses apart

| Response | Meaning |
|---|---|
| `404` + `path: /api/v1/request//` | Empty `request_id` - you sent `data: {}` |
| `404` + `Request not found.` | **The key is valid**, that request ID does not exist |
| `403` + `You do not have permission` | Invalid API key |
| `200` | Success |

The second `404` is a good sign: authentication succeeded.

---

### Everything returns 403

1. Check the key: **Seerr** -> **Settings** -> **General** -> **API Key**.
2. Check that **CSRF Protection is disabled** in Seerr settings.
3. Check that the `rest_command` block actually loaded - see the slug error
   above. Stale in-memory definitions with an old key produce exactly this.

---

## Seerr status issues

### Status stuck on "Requested"

The *Requested -> Available* transition does not come from Radarr. The chain is:

```
Radarr imports the file -> Jellyfin scans the library -> Seerr scans Jellyfin
```

With symlink-based setups Jellyfin often does not get a change notification and
waits for its periodic scan, so a delay is not a bug.

To force it:

1. **Jellyfin** -> **Scan Libraries**.
2. **Seerr** -> **Settings** -> **Jellyfin** -> **Sync Libraries**.

If the status still does not move, the library is most likely not enabled for
synchronisation in the Seerr settings.

---

### No events arrive at all

1. Confirm `event.overseerr_last_media_event` exists and is not `unavailable`.
2. Confirm **CSRF Protection is disabled** - the integration cannot register its
   webhook otherwise.
3. Reload the Seerr integration: it re-registers the webhook in Seerr on every
   reload. Do not edit that webhook manually; it will be overwritten.
4. Make sure Seerr can reach your Home Assistant URL (the webhook is Seerr ->
   Home Assistant, so the *internal* URL under **Settings** -> **System** ->
   **Network** must be reachable from the Seerr host).

---

### My own requests never produce a notification

Admin accounts usually have auto-approve permission, so their requests arrive as
`auto_approved`, not `pending`. Test with a regular user account.
