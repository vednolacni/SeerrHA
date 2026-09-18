# Changelog

All notable changes to this project are documented in this file.

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
