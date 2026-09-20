# Changelog

All notable changes to this project are documented in this file.

## [1.4.0] - 2026-09-20

### Removed

- Blueprint input **REST command**. Now that the Seerr URL is an input, a
  single `rest_command.seerrha_request_action` serves every server, so the name
  never needed changing - it was a field to scroll past. The action is
  hardcoded. Automations that left it at the default are unaffected; one that
  set it explicitly must be re-created.

### Changed

- **Notify service (advanced)** now opens with "leave this empty if you picked
  a Phone above", instead of leaving people wondering whether both are needed.

## [1.3.0] - 2026-09-19

### Added

- Blueprint input **Phone**: a device picker listing only devices running the
  Companion app. A plain text selector never offers suggestions, so the notify
  service had to be typed from memory. **Notify service** is still there as
  **Notify service (advanced)** and takes priority when set, for the one case
  the picker cannot express - a notification group covering several phones.

### Changed

- **The Seerr URL and API key are blueprint inputs now.**
  `examples/rest_commands.yaml` is copied unchanged: the command takes
  `base_url` and `api_key` from the caller, so `IP_SEERR` and the `!secret`
  lookup are gone from the file. Setup on the blueprint route no longer
  involves editing any YAML.
- The API key is no longer read from `secrets.yaml` by default. Keeping it
  there is still supported and documented - set the `X-Api-Key` header to
  `!secret seerr_api_key` and leave the blueprint field blank - but it is now
  opt-in rather than required.
- The package, the standalone example automation and the helper script gather
  their settings into a `variables:` block at the top, so each has one place to
  edit instead of values scattered through the file.

### Notes

- Blueprint inputs are stored in plain text in `automations.yaml` and appear in
  automation traces, so the API key now reaches backups and diagnostics
  downloads. This is a deliberate trade for a setup that needs no file editing;
  the `!secret` route above avoids it.

### Breaking

- `rest_command.seerrha_request_action` and `seerrha_test` now require
  `base_url` and `api_key` from the caller. Replace your `rest_commands.yaml`
  with the new copy and re-open the automation to fill in the two new fields.
  Calls made by hand need both values passed in `data`.

## [1.2.0] - 2026-09-19

### Fixed

- **`rest_command` does not need a restart after the first one.** Every guide
  in this repository said a new or renamed command required a full restart.
  It does not: `rest_command` registers a reload handler that drops all
  commands and re-reads the YAML. Only the very first `rest_command:` key needs
  a restart, because the integration is not loaded before it exists. The
  confusion came from *Reload core configuration*, which genuinely does not
  touch `rest_command` - `rest_command.reload` is the one that does.

- **The decision result is now checked before the notification is cleared.**
  `rest_command` only logs a warning on a 4xx/5xx, so a failed approve used to
  clear the prompt and report "Request #35 approved." while the request stayed
  pending in Seerr. The blueprint, the package and the example automation now
  read `response_variable`, keep the notification up on failure and report the
  HTTP status.
- Removed the `notify.mobile_app_your_phone` default from the blueprint's
  **Notify service** input. It was a default that could not work, so the
  automation could be saved in a silently broken state. The field is now
  required.

### Added

- Blueprint input **Action prefix** (default `SEERR`). The
  `mobile_app_notification_action` event carries no device information, so every
  automation built from this blueprint reacts to every button press and two of
  them would send the decision twice. A per-instance prefix keeps them apart.
  Documented alongside the simpler fix: one automation, one notification group.
- `llms.txt` section 7 documents the `overseerr.get_requests` response: the
  required `config_entry_id`, `id` vs the webhook's `request_id`, and
  `media.title` / `media.name` with no `media.tmdb_id`. Without this an
  assistant reading `llms.txt` regenerated the bug fixed in 1.1.0.
- Troubleshooting entries for Android notification channels being immutable
  after creation, and for decisions being sent twice.

### Changed

- The smoke test reads `GET /api/v1/request?take=1` instead of a hardcoded
  request ID 35, so a valid key returns `200` whatever exists. The docs no
  longer have to explain why a `404` was the good outcome.
- Replaced the vague "the Companion app does not reliably forward `tag`" with
  the actual payload: `tag` is Android-only, `action_data` is iOS-only, and
  there is no `device_id` at all.
- The package header states what it leaves out compared with the blueprint.

## [1.1.0] - 2026-09-18

### Fixed

- The "Import blueprint" My Home Assistant badge returned *Invalid parameters
  given*. The `blueprint_import` redirect takes `blueprint_url`, not
  `blueprint`.
- `examples/automations/seerr_pending_reminder.yaml` could not run: the
  `overseerr.get_requests` action requires `config_entry_id`, which was missing,
  and it listed `media.tmdb_id`, which does not exist on the response (the
  integration replaces `media` with the full TMDB details). It now passes the
  config entry and lists real titles, request IDs and requesters.

### Changed

- Reframed the project as an add-on to the official Seerr (`overseerr`)
  integration rather than to a whole media stack. Jellyfin / Plex / Radarr /
  Sonarr specifics that Home Assistant cannot observe or control were dropped
  from the docs.
- Replaced the personal `matic_s_phone` and requester samples with neutral
  placeholders, and documented every placeholder and where to find the real
  value in the README.
- Moved the design decisions out of the README into
  `docs/event-reference.md`, and trimmed the setup steps the README duplicated
  from `docs/setup.md`.
- Credited `vaparr/ha-overseerr` as the origin of the approach, with what
  changed since.
- CI: `actions/checkout` v4 -> v5 (v4 pins the deprecated Node 20).

### Removed

- `examples/dashboards/pending_requests_card.yaml`. Lovelace does not render
  Jinja templates in card configuration, so its Approve / Decline buttons sent
  the template as a literal string instead of a request ID. `examples/README.md`
  now explains why there is no dashboard card.

## [1.0.0] - 2026-09-18

### Added

- Automation blueprint `seerr_request_approval.yaml` with UI inputs for the
  event entity, REST command, notify service, button labels, notification
  channel, sticky flag, confirmation notification and availability alerts.
- `packages/seerrha.yaml` - REST commands and automation in a single package
  file for people who prefer YAML over blueprints.
- `examples/rest_commands.yaml` with the `approve` / `decline` command and a
  read-only smoke test, using `!secret seerr_api_key`.
- Example automations: request approval, media available notification, daily
  pending requests reminder.
- Example script `seerr_decide_request.yaml` (approve or decline by ID, reports
  the HTTP status back).
- Example dashboard card showing the last Seerr event with approve/decline
  buttons.
- Documentation: setup guide, event and data reference, troubleshooting & FAQ.
- `llms.txt` as AI assistant context.
- CI: yamllint and a blueprint sanity check (`scripts/check_blueprint.py`).
