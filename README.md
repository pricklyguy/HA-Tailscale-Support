# Prickly Guy Remote Support for Home Assistant

Client-controlled, time-limited remote support access using Tailscale OAuth and device tags.

## Features
- ✅ OAuth tokens that never expire (auto-refresh every 50 minutes)
- ✅ Client controls access with simple toggle switch
- ✅ Auto-timeout after configurable period (0.5 - 8 hours)
- ✅ Visual notifications on all devices
- ✅ Secure tag-based access control
- ✅ Client phones/tablets never affected

## What This Does
Allows you to provide secure, time-limited remote support to Home Assistant installations without requiring clients to manage expiring API keys. Clients control when you have access with a simple dashboard toggle.

## Requirements
- Home Assistant with packages enabled
- Tailscale account (free tier works)
- Tailscale add-on installed in Home Assistant

## Installation
See [INSTALLATION.md](INSTALLATION.md) for complete step-by-step instructions.

## Quick Start
1. Drop `pg_support.yaml` into `/config/packages/`
2. Follow the [installation guide](INSTALLATION.md)
3. Client toggles support access when needed
4. Access automatically expires after timeout

## Support
Created by **Prickly Guy** for family, friends, and clients.

Questions? Contact: Support@Pricklyguy.com

## License
MIT License - Feel free to use and modify!
