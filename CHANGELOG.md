# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- GitHub Actions validation with HACS Action and Home Assistant Hassfest.
- Reauthentication flow for expired or changed Iliad credentials.
- Reconfiguration flow for the friendly SIM name and credentials.
- Dedicated cookie session for every configured Iliad account, including config-flow validation, to keep multiple SIM sessions isolated.
- HACS metadata for Italy and Home Assistant 2026.8.x.

### Changed
- The integration is now designed as a generic multi-SIM, multi-instance Home Assistant integration rather than a project-specific component.
- Stable account identifiers are derived from a non-plain-text SHA-256 digest of the Iliad account ID.

## [0.2.0] - release candidate

### Added
- UI configuration through Home Assistant config entries.
- Multiple Iliad accounts/SIMs in the same Home Assistant instance.
- Sensors for available credit, used data and remaining data.
- Async Iliad account client and `DataUpdateCoordinator`.
- Stable entity unique IDs and a dedicated device for each configured account.
- Manual and HACS custom-repository installation structure.

### Notes
- `0.2.0` has not yet been validated with a real Iliad account.
- The current implementation parses the Iliad personal-area HTML and may require updates if Iliad changes the portal structure.
