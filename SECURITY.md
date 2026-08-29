# Security policy

## Scope

This project handles credentials for the Iliad Italia personal area. Those credentials are used only to authenticate against `https://www.iliad.it/` and must never be included in issues, logs, test fixtures or repository files.

The integration is unofficial and parses the Iliad personal-area HTML. It does not intentionally send credentials, cookies or account-page contents to any third party.

## Sensitive data

Never publish any of the following in a GitHub issue, pull request or discussion:

- Iliad username/account ID;
- password;
- session cookies or authentication headers;
- browser HAR files;
- complete HTML captured from a real account;
- screenshots containing identifiers you do not want to disclose.

Real account captures used to investigate parser changes must be anonymized before being turned into test fixtures.

## Reporting a vulnerability

Do not open a public issue for a vulnerability that could expose credentials, cookies or account data.

Prefer GitHub's private security-reporting mechanism for this repository when available. If private reporting is not available, contact the maintainer privately before publishing technical details.

Include only the minimum information needed to reproduce the issue and remove all real credentials and session material.

## Repository safeguards

The project intentionally:

- keeps a separate cookie jar/session for each configured account;
- does not log credentials or raw account HTML;
- exports diagnostics without Iliad account identifiers, exact credit or exact data-usage values;
- uses only HTTPS Iliad endpoints;
- ignores common local secret, cookie, HAR and real-account capture files;
- pins GitHub Actions used by CI to immutable commit SHAs where practical.

## User responsibility

Home Assistant stores integration credentials in its config-entry storage. Protect the Home Assistant instance, backups and host filesystem accordingly. Anyone with administrative access to the Home Assistant configuration may be able to access stored integration credentials.
