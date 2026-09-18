# Event & Data Reference

Everything the automations read comes from a single entity:

```
event.overseerr_last_media_event
```

The Seerr integration updates it every time its webhook fires.

---

## Attribute structure

The attributes are **nested**, not flattened:

```yaml
event_type: pending          # pending, approved, available, failed, declined, auto_approved
event: New Movie Request
subject: "Spider-Man: Brand New Day (2026)"
message: "..."               # overview text
entity_picture: "https://image.tmdb.org/t/p/w600_and_h900_bestv2/....jpg"
media:
  media_type: movie          # movie | tv
  imdb_id: ""
  tmdb_id: 969681
  tvdb_id: null
  jellyfin_media_id: ""
  status: pending
  status4k: unknown
request:
  request_id: 35
  requested_by_email: moviebuff@example.com
  requested_by_username: MovieBuff
  requested_by_avatar: "/avatarproxy/..."
  requested_by_jellyfin_user_id: "..."
extra: []                    # TV: [{name: "Requested Seasons", value: "3, 4, 5"}]
```

**The poster is already in `entity_picture`.** No TMDB lookup is needed.

---

## Reading the values

| Value | Template |
|---|---|
| Event type | `trigger.to_state.attributes.event_type` |
| Title | `trigger.to_state.attributes.subject` |
| Poster | `trigger.to_state.attributes.entity_picture` |
| Request ID | `trigger.to_state.attributes['request']['request_id']` |
| Requester | `trigger.to_state.attributes['request']['requested_by_username']` |
| Media type | `trigger.to_state.attributes['media']['media_type']` |
| TMDB ID | `trigger.to_state.attributes['media']['tmdb_id']` |
| Requested seasons | see below |

Requested seasons only exist for TV requests and live in the `extra` list:

```jinja
{{ trigger.to_state.attributes.extra
   | selectattr('name', 'eq', 'Requested Seasons')
   | map(attribute='value') | first | default('', true) }}
```

> Always read from `trigger.to_state`, never from `state_attr()`. The entity can
> already be overwritten by the next event while your automation is still
> running.

---

## Event types

| `event_type` | Meaning |
|---|---|
| `pending` | New request waiting for a decision - this is the one that triggers a notification |
| `auto_approved` | Request from a user with auto-approve permission (admins) |
| `approved` | Request was approved (by you, by the web UI, or by this automation) |
| `declined` | Request was declined |
| `available` | Content is ready to play - Seerr has seen it in the library |
| `failed` | The download or import failed downstream of Seerr |

Only `pending` (and optionally `available`) is acted on. The rest arrive on the
same entity and are filtered out by the automation's condition.

---

## REST API endpoints used

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/request/{id}/approve` | Approve |
| `POST` | `/api/v1/request/{id}/decline` | Decline |
| `GET` | `/api/v1/request/{id}` | Read a single request (used by the smoke test) |

Authentication is the `X-Api-Key` header. All three need
**CSRF Protection disabled** in Seerr.

---

## Notification action names

The request ID is encoded **in the action name**, not in the `tag`:

```
SEERR_APPROVE_35
SEERR_DECLINE_35
```

The Companion app does not reliably forward the `tag` field in the
`mobile_app_notification_action` event on both platforms; the action name always
comes through. It is parsed with `split('_')[2]`.

The `tag` is still set (`seerr_35`) - it is what makes
`message: clear_notification` dismiss the right notification afterwards.

---

## Design decisions

**The request ID lives in the action name**, not in `tag` - see above. It also
carries a `SEERR_` prefix so it cannot collide with bare `approve` / `deny`
actions from other notifications on the same phone.

**One automation with `choose`**, not two. Both triggers share a context, so the
notify service is defined once.

**`mode: queued` is mandatory.** With several requests arriving at once, none is
dropped.

**Data comes from `trigger.to_state`**, never from `state_attr()`. The entity can
already be overwritten by the next event while the automation is still running.

**Never store the whole attribute dictionary in a variable.** It contains
`EventEntityStateAttribute.*` enum keys, so Home Assistant renders it as a
string and every later `.request` access raises `UndefinedError`. Store concrete
fields instead - see
[Troubleshooting](troubleshooting.md#template-issues).
