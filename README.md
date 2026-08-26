# Prickly Guy Remote Support for Home Assistant

Client-controlled, time-limited remote support access using Tailscale and Home Assistant.

## v2 — Home Assistant App

This branch contains the modernization of Prickly Guy Remote Support into a native Home Assistant App (formerly called an add-on).

The goal is simple: **install the app, configure Tailscale once, and give the homeowner one obvious button to allow or revoke remote support.**

### v2 features

- Native Home Assistant App installation
- Home Assistant Ingress — no extra port forwarding or exposed web UI
- Tailscale OAuth client credentials
- Modern least-privilege `devices:core` API scope
- Short-lived Tailscale API tokens automatically renewed by the app
- Client-controlled support sessions
- Automatic timeout from 30 minutes through 8 hours
- Existing Tailscale tags saved and restored
- No changes to the Tailscale ACL/policy file
- No Card Mod requirement
- Persistent session recovery after an app restart

## Current status

**v2 is experimental.** The original YAML package remains on `main` while the new App is developed and tested on the `v2-app-modernization` branch.

## Architecture

```text
Home Assistant
      │
      │ Home Assistant Ingress
      ▼
Prickly Guy Remote Support App
      │
      ├── OAuth token management
      ├── Session timer
      ├── Tag backup / restore
      └── Tailscale API
               │
               ▼
          Tailscale device
```

The app does not modify the tailnet policy. Access is controlled by the tags already defined in the tailnet policy.

## Tailscale requirements

Create a Tailscale OAuth client/trust credential with the `devices:core` write scope and permission to manage the support/client tags.

The app needs:

- OAuth client ID
- OAuth client secret
- Tailscale device ID for the Home Assistant host
- Client tag, normally `tag:client-device`
- Support tag, normally `tag:support-enabled`

Tailscale API access tokens expire after one hour. The app obtains a fresh token automatically instead of storing a long-lived API access token.

## Development

The v2 App lives in `tailscale_support/` and is intentionally marked `experimental` until it has been tested against current Home Assistant OS releases on both amd64 and aarch64.

See [`tailscale_support/DOCS.md`](tailscale_support/DOCS.md) for the current setup and testing notes.

## Legacy version

The original package-based implementation remains available in `pg_support.yaml` and `Installation.md` while v2 is being developed.

## Support

Created by **Prickly Guy** for family, friends, and clients.

Questions? Contact: Support@PricklyGuy.com

## License

MIT License - Feel free to use and modify!
