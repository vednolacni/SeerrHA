# Changelog

All notable changes to this project are documented in this file.

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
