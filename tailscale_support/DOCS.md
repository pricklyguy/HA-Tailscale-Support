# Prickly Guy Remote Support v2

Client-controlled, time-limited Tailscale access for Home Assistant.

## What changed in v2

Version 2 moves the support-control logic out of a Home Assistant YAML package and into a native Home Assistant App (formerly called an add-on).

The app:

- Keeps the short-lived Tailscale OAuth access token in memory.
- Automatically obtains a fresh token before the previous one expires.
- Uses the modern `devices:core` Tailscale scope rather than a broad API key.
- Saves the device's existing Tailscale tags before enabling support.
- Replaces the device tags with the support tag while support is active.
- Restores the original tags when support ends.
- Automatically ends the session after the configured timeout.
- Persists only the session state needed to recover safely after an app restart.
- Provides its UI through Home Assistant Ingress, so no additional port forwarding is required.

## Tailscale setup

Create a Tailscale OAuth client/trust credential with the `devices:core` write scope and permission to manage the tags used by this app.

You will need:

- OAuth client ID
- OAuth client secret
- Home Assistant device ID as shown by the Tailscale admin console
- The client tag, normally `tag:client-device`
- The support tag, normally `tag:support-enabled`

The OAuth client secret is stored as a Home Assistant App password option and is never displayed by the app UI.

## Recommended policy model

Use a deny-by-default Tailscale policy and grant the support identity access only to `tag:support-enabled` on TCP port 8123.

The app deliberately does not modify the Tailscale policy file. It only changes the tags on the Home Assistant device.

## Important tag behavior

Tailscale's device tag API replaces the device's existing tags. v2 therefore records the current tag set before enabling support and restores that exact set when support is disabled.

Make sure the OAuth credential is allowed to manage the support and client tags before testing the app.

## Testing

This branch is intentionally marked `experimental` and should be tested on a non-production Home Assistant installation first.

For local app testing, copy the app directory into `/addons` on a test Home Assistant system, or use the Home Assistant local app repository workflow.
