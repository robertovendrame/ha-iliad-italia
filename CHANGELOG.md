# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.4.0-beta.2] - 2026-08-25

### Fixed
- Added a second renewal-date strategy based on the real Iliad `Periodo di riferimento dal ... al ...` text.
- When the explicit `Si rinnova il ...` date is not present in the static HTML, the integration now derives the renewal date as the day after the current reference-period end date.

### Validated
- Real Iliad page observed with renewal date `03/09/2026` and reference period ending `02 Settembre 2026`; the new fallback is designed specifically for this real page structure.

### Notes
- This remains a beta release until the fallback is confirmed in Home Assistant with real account data.

## [0.4.0-beta.1] - 2026-08-24

### Added
- Renewal-date parsing from the Iliad `Consumi e Credito` page without relying on a new hard-coded CSS selector.
- `Data rinnovo` and `Giorni al rinnovo` sensors.
- Estimated average daily data usage for the current offer period.
- Daily data budget available until renewal.
- Projected remaining data at renewal based on the current average usage pace.
- `Rischio esaurimento prima del rinnovo` problem binary sensor.
- Renewal date included in privacy-safe diagnostics.

### Notes
- This is a beta release intended for real-world validation of renewal-date parsing and projection entities.
- Projection values are estimates derived locally from current-period usage, remaining data and the monthly renewal date; they are not values provided directly by Iliad.
- If the renewal date is not recognized, the renewal/projection entities may be unavailable while the existing credit and traffic sensors continue to work.

## [0.3.0] - 2026-08-24

### Added
- GitHub Actions validation with Python syntax check, HACS Action and Home Assistant Hassfest.
- Reauthentication flow for expired or changed Iliad credentials.
- Reconfiguration flow for the friendly SIM name and credentials.
- Dedicated cookie session for every configured Iliad account, including config-flow validation, to keep multiple SIM sessions isolated.
- HACS metadata for Italy and Home Assistant 2026.8.x.
- Calculated total data sensor (`used + remaining`).
- Used-data percentage sensor.
- Remaining-data percentage sensor.
- Last successful update timestamp sensor.
- Per-SIM `Aggiorna ora` button for an immediate manual refresh.
- Per-SIM configurable remaining-data threshold in GB.
- Per-SIM configurable remaining-data threshold in percent.
- `Dati in esaurimento` problem binary sensor, activated when either configured data threshold is reached.
- Per-SIM configurable low-credit threshold in EUR.
- `Credito basso` problem binary sensor.
- Per-SIM configurable polling interval from 1 to 24 hours, with 6 hours as default.
- Privacy-safe Home Assistant diagnostics without Iliad username or password.

### Changed
- The integration is now designed as a generic multi-SIM, multi-instance Home Assistant integration rather than a project-specific component.
- Stable account identifiers are derived from a non-plain-text SHA-256 digest of the Iliad account ID.
- README updated after successful real-world testing with two Iliad accounts in the same Home Assistant instance.

### Validated
- Login and account parsing with real Iliad credentials.
- Credit, used-data and remaining-data retrieval.
- Two distinct Iliad accounts working simultaneously in the same Home Assistant instance without session/cookie conflicts.
- HACS and Hassfest validation passing before release.

## [0.2.0] - development milestone

### Added
- UI configuration through Home Assistant config entries.
- Multiple Iliad accounts/SIMs in the same Home Assistant instance.
- Sensors for available credit, used data and remaining data.
- Async Iliad account client and `DataUpdateCoordinator`.
- Stable entity unique IDs and a dedicated device for each configured account.
- Manual and HACS custom-repository installation structure.

### Notes
- `0.2.0` was used as a development milestone before the first published release.
- The current implementation parses the Iliad personal-area HTML and may require updates if Iliad changes the portal structure.
