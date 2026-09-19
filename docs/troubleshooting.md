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

You almost certainly used the wrong reload. **Reload core configuration** (and
the old "Reload YAML configuration" button) does not touch `rest_command`.

`rest_command` does have its own reload. Use whichever you prefer:

- **Developer Tools** -> **Actions** -> `rest_command.reload`
- **Developer Tools** -> **YAML** -> **RESTful Command**
- **Developer Tools** -> **YAML** -> **All YAML configuration**

It drops every existing command and re-reads them from your configuration,
`!include`s and all.

**The one exception is the first time.** If `rest_command:` was not in
`configuration.yaml` at the last startup, the integration was never loaded, so
`rest_command.reload` does not exist yet either. That first time needs a real
**restart**; after that, reloading is enough.

Automations are different again - they refresh as soon as you save them.

---

## Notification issues

### No image and no buttons on the notification

You are calling a notify **entity** instead of a notify **action**.

- `notify.your_phone` (entity) - supports only `send_message`. No image, no
  actions.
- `notify.mobile_app_your_phone` (action) - full Companion payload.

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

### Changing the channel sound or importance does nothing

Android notification channels are created once and are then **immutable** - the
`importance` in the payload is only read when the channel first appears. After
that, the channel is owned by Android and only the user can change it, under
the Companion app's notification settings on the phone.

To get a fresh channel from Home Assistant, set a different **Notification
channel** name in the blueprint. The old one stays behind until you remove it
on the phone.

---

### Every decision is sent to Seerr twice

You have more than one automation built from the blueprint. The button press
arrives as a plain event with no device information, so all of them react to
it. Give each automation its own **Action prefix** (under *Optional extras*),
or better, use one automation pointed at a notification **group** covering
every phone.

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
| `200` | Success |
| `404` + `path: /api/v1/request//` | Empty `request_id` - you called the approve/decline command with `data: {}` |
| `404` + `Request not found.` | **The key is valid**, that request ID does not exist |
| `403` + `You do not have permission` | Invalid API key, or CSRF protection still on |

`rest_command` does not fail the automation on a `4xx`/`5xx` - it only logs a
warning. That is why the automation reads `response_variable` and checks the
status before clearing the notification; otherwise a failed approve would look
like it worked.

---

### Everything returns 403

1. Check the key: **Seerr** -> **Settings** -> **General** -> **API Key**.
2. Check that **CSRF Protection is disabled** in Seerr settings.
3. Check that the `rest_command` block actually loaded - see the slug error
   above. Stale in-memory definitions with an old key produce exactly this.

---

## Event issues

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

---

### The "available" notification arrives late, or not at all

`available` is emitted by Seerr once it sees the finished item in your media
library, which happens on its own schedule well after the approval. Nothing in
Home Assistant influences that timing - if the event never fires, the question
belongs on the Seerr side, not here.
