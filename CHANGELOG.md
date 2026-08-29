# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.5.0] - 2026-08-29

### Added
- Parsing of the commercial Iliad offer name.
- Official data allowance (`Plafond dati`) when exposed by the Iliad account page.
- Offer renewal price (`Costo offerta`).
- New `Offerta`, `Plafond dati` and `Costo offerta` sensors.
- Offer metadata in privacy-safe diagnostics.
- Automatic parser regression tests with anonymized realistic HTML fixtures.
- GitHub issue forms for bug reports and feature requests.

### Changed
- Used-data and remaining-data percentages now prefer the official Iliad allowance when available, falling back to `used + remaining` on unsupported/older layouts.
- `Dati totali calcolati` remains available as a compatibility and diagnostic value rather than the preferred denominator.
- GitHub Actions validation now runs Python syntax checks, `pytest`, HACS validation and Home Assistant Hassfest.

### Fixed
- Hardened offer-name extraction for split DOM markup and generic portal labels such as `offerta mobile`.
- Prefer specific and concise offer-name candidates over contaminated parent nodes.
- Strip decorative separators such as `●`, `•`, `·` and `|` from the parsed offer name.
- Tightened renewal-date parsing so unrelated dates in the reference-period text cannot be selected as the renewal date.

### Validated
- Official allowance `350 GB` and renewal price `14.99 EUR` confirmed on a real Iliad account.
- Offer-name parser regression suite passes after fixes developed through beta.1 to beta.4.
- Multi-account behavior and different renewal/reference periods remain supported from the validated 0.4.x implementation.

## [0.5.0-beta.4] - 2026-08-28

### Fixed
- Real-world validation of beta.3 showed the commercial offer name being parsed correctly but retaining the trailing black-circle separator (`Offerta Dati 350 ●`).
- Offer-name normalization now treats `●`, `•`, `·` and `|` as decorative separators and strips them from both DOM-derived and fallback offer labels.
- Added a regression test for `Offerta Dati 350 ● Credito: ...`, which must resolve exactly to `Offerta Dati 350`.

## [0.5.0-beta.3] - 2026-08-25

### Fixed
- Real-world validation of beta.2 showed the offer sensor resolving to the generic portal label `offerta mobile` instead of the commercial offer name.
- Offer parsing now collects multiple DOM candidates and scores them, preferring specific labels containing plan details/numbers over generic navigation labels such as `offerta mobile`.
- Parent DOM nodes are inspected so split markup such as `Offerta` + `Dati 350` can still resolve to `Offerta Dati 350`.
- Added a regression test where a generic `offerta mobile` label appears before a split `Offerta Dati 350` heading.

### Validated
- On the real beta.2 test account, `Plafond dati` = `350 GB` and `Costo offerta` = `14.99 EUR` remain correct; only offer-name selection required this fix.

## [0.5.0-beta.2] - 2026-08-25

### Fixed
- Hardened offer-name parsing after real Home Assistant validation showed `Offerta` as unknown while `Plafond dati` and `Costo offerta` were parsed correctly.
- The parser now prefers the smallest DOM text node containing the offer label instead of relying only on the flattened page text and proximity to `Credito`.
- Added a regression test where `Offerta Dati 350` is isolated in its own nested DOM node and unrelated text appears before the credit label.

### Validated
- Real account validation of `0.5.0-beta.1`: official allowance `350 GB` and renewal price `14.99 EUR` parsed correctly; offer name required this follow-up fix.

## [0.5.0-beta.1] - 2026-08-25

### Added
- Offer-name parsing from the real Iliad account page.
- Official data allowance parsing from the `used / total` traffic value.
- Offer renewal price parsing from the `Si rinnova ... a ... €` text.
- New `Offerta`, `Plafond dati` and `Costo offerta` sensors.
- Offer metadata included in privacy-safe diagnostics.
- Parser regression tests with anonymized realistic HTML fixtures.
- Automatic `pytest` execution in the GitHub Actions validation workflow.
- GitHub issue forms for bug reports and feature requests, including privacy guidance.

### Changed
- Data-used and data-remaining percentages now prefer the official Iliad allowance when it is available, falling back to `used + remaining` for older or unsupported page layouts.
- `Dati totali calcolati` is kept as a separate compatibility/diagnostic value and is no longer the preferred denominator when an official allowance is parsed.

### Notes
- This beta requires real-world validation of offer name, official allowance and renewal price across the two already configured test accounts.
- The parser keeps the previous behavior when the new commercial metadata is not present in the HTML.

## [0.4.0] - 2026-08-25

### Added
- Renewal-date parsing from the Iliad `Consumi e Credito` page.
- Direct parsing of the real Iliad `Periodo di riferimento dal ... al ...` start and end dates.
- `Data rinnovo`, `Giorni al rinnovo`, `Inizio periodo` and `Fine periodo` sensors.
- Estimated average daily data usage for the current offer period.
- Daily data budget available until renewal.
- Projected remaining data at renewal based on the current usage pace.
- `Rischio esaurimento prima del rinnovo` problem binary sensor.
- Renewal date and reference-period dates included in privacy-safe diagnostics.

### Changed
- Average daily usage and projected remaining data now use the real Iliad reference-period start date when available.
- The previous-month calculation is retained only as a compatibility fallback when the reference period cannot be parsed.
- Renewal-date fallback derives renewal as the day after the parsed reference-period end date when the explicit renewal date is not available in the static HTML.

### Validated
- Renewal and reference-period parsing confirmed with two real Iliad accounts in the same Home Assistant instance.
- Account 1 confirmed with reference period `02/08/2026` to `02/09/2026` and renewal `03/09/2026`.
- Account 2 confirmed with reference period `09/08/2026` to `09/09/2026` and renewal `10/09/2026`.
- Projection entities populate correctly on both tested accounts.

### Notes
- Projection values are estimates derived locally from current usage, remaining data and the current reference period; they are not values provided directly by Iliad.

## [0.4.0-beta.3] - 2026-08-25

### Added
- Direct parsing of the real Iliad `Periodo di riferimento dal ... al ...` start and end dates.
- New `Inizio periodo` and `Fine periodo` date sensors.
- Reference-period dates included in privacy-safe diagnostics and in the projected-exhaustion binary sensor attributes.

### Changed
- Average daily usage and projected data at renewal now use the real Iliad reference-period start date when available, instead of assuming the previous monthly renewal date.
- The previous-month calculation is retained only as a compatibility fallback when the reference period cannot be parsed.
- Renewal-date fallback now reuses the parsed reference-period end date and derives renewal as the following day.

### Validated
- Real Iliad page observed with `Periodo di riferimento dal 02 Agosto 2026 al 02 Settembre 2026` and renewal on `03/09/2026`.

## [0.4.0-beta.2] - 2026-08-25

### Fixed
- Added a second renewal-date strategy based on the real Iliad `Periodo di riferimento dal ... al ...` text.
- When the explicit `Si rinnova il ...` date is not present in the static HTML, the integration now derives the renewal date as the day after the current reference-period end date.

## [0.4.0-beta.1] - 2026-08-24

### Added
- Renewal-date parsing from the Iliad `Consumi e Credito` page without relying on a new hard-coded CSS selector.
- `Data rinnovo` and `Giorni al rinnovo` sensors.
- Estimated average daily data usage for the current offer period.
- Daily data budget available until renewal.
- Projected remaining data at renewal based on the current average usage pace.
- `Rischio esaurimento prima del rinnovo` problem binary sensor.
- Renewal date included in privacy-safe diagnostics.

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
