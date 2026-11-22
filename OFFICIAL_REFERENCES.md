# Official references used to frame the deployment

Checked 2026-11-12. These are operational documentation references, not proof that live services are connected.

- Discord server templates: https://support.discord.com/hc/en-us/articles/360041033511-Server-Templates (categories/channels/roles/permissions; not chats, members, bots, or certain Community channel types)
- Discord app installation: https://discord.com/developers/docs/quick-start/getting-started (guild install, scopes and granular bot permissions)
- Discord app commands: https://docs.discord.com/developers/docs/interactions/slash-commands
- Discord bot data access: https://support.discord.com/hc/en-us/articles/7933951485975-Visibility-of-Bot-Data-Access
- Discord 2026 API data access change: https://discord.com/blog/updated-requirements-to-how-apps-access-data-in-servers
- Google Drive resumable uploads: https://developers.google.com/workspace/drive/api/guides/manage-uploads (future direct-cloud adapter; current implementation uses rclone mirror)
- Google Shared Drive support: https://developers.google.com/workspace/drive/api/guides/enable-shareddrives
- Tailscale private Docker service: https://tailscale.com/docs/solutions/host-private-server-docker

Third-party music bots, moderation bots and event bots must each be evaluated for access, retention and actual integration capabilities. The current HERMES code does **not** play or relay music.
