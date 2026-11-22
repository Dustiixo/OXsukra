# HERMES integration catalogue (research and candidates)

Research snapshot: 2026-11-12. **Catalogued does not mean installed, approved, connected, or reviewed for safety.** App listings advertise functionality; availability, subscription terms, API access, legality of streaming sources and permissions can change.

## Principle: one responsible orchestrator, independent service adapters

Do **not** build an automation by having one Discord bot impersonate a human and type commands for another bot. Discord app commands belong to each app; cross-app bot interoperability is not guaranteed. A valid adapter needs a supported API, webhook or documented interface and its own approved permissions. For simple notifications, outgoing webhooks are enough. For interactions, use the official Discord bot/API.

| Need | Candidate or platform | What it offers | Integration recommendation |
|---|---|---|---|
| Music and parties | SeshTunes | DJ controls, player UI, radio, multi-player claims | Trial separately; choose based on actual required privileges, policy and quality |
| Music and playlists | Vocard | Music queues, app UI, playlist support | Separate bot, not automatically owned by HERMES |
| Local/community audio | GEEK Music | `/play-file` user-file playback advertised | Review music rights and bot upload/privacy policy before use |
| Spotify listening | Native Spotify Listen Along | Invite friends to listen in synchrony | Premium needed for listeners; doesn't authorize a Discord audio rebroadcast |
| Moderation | Discord AutoMod | Native rule-based protections | Start here, before adding overlapping moderation bots |
| Roles and moderation | Carl-bot, Dyno | Role/menu moderation / broader utilities | Install only if default moderation lacks a needed feature |
| Events and meetings | Sesh / Apollo-style scheduling | RSVP/calendar reminders | HERMES stores approved references, not member activity profiles |
| Tickets and proposals | Sortr / Ticket Tool | Private forms, triage, tickets | Ticket export should be opt-in; never archive everyone by default |
| Visual/voice activities | Discord Activities | Whiteboards, games, collaborative sessions | Run independently inside Discord, no automatic recording |
| Workflow editor | n8n | Webhook, HTTP, app/notification actions | Future broker for allowlisted workflow IDs, never direct shell commands |
| Home alerts | Home Assistant's Discord integration | Sends Discord notifications | Output-only; it is not an inbound Discord command trigger |
| Shared knowledge | Obsidian Markdown | Local knowledge vault, searchable files | One-way approved export first, avoid conflicting writers |
| Code and releases | GitHub App/webhooks | Repo issues, releases, CI statuses | Implement official signed webhooks and scoped tokens in later gate |
| Storage | Google Drive via rclone | Optional mirroring of verified bytes | Dedicated shared folder, least privileges, retry/verify changes |
| Local AI | Ollama or other local model | User-controlled inference | Use only selected documents, never silently index whole conversations |

## Required review checklist for any bot

1. **Identity/owner:** vendor, website, support, policy and maintainer.
2. **Requested permissions:** why does a music bot need Administrator or Read Messages? Decline excess access unless there is a documented and accepted reason. Review Discord's Data Access tab.
3. **Data scope:** messages, messages metadata, voice-channel presence, member list, command content, external music requests.
4. **Data destinations:** provider's cloud, our hub, user's client, external music platform.
5. **Persistence:** retention, exports, deletion, account removal.
6. **Interface:** direct API, webhook, standalone third-party app, or *no* external API (manual use only).
7. **Safety:** no arbitrary shell execution, no token forwarding, no forced AI training, no covert recording, no DRM bypass.
8. **Test:** staging server, limited roles, sample files and tracks, disable/rollback.

## Operating examples

**Friday music night:** Members manually queue tracks in the chosen music bot. Optionally a consenting member uses HERMES `/funnel_note` to save a playlist link or feedback. The hub does not archive the audio or automatically capture participants.

**Research handoff:** Developer uploads a ZIP using local Funnel; checksum and job are recorded; HERMES may send the configured notification; reviewers explicitly create an Alchemy proposal, then source-linked findings become proposed Markdown notes.

**Business concept:** A member may submit a non-sensitive `business.idea_submitted` metadata-only event. Detailed budgets, credentials, plans and confidential contributions remain **off the shared v0.2 hub** until project-level ACL, roles and deletion are implemented and verified.

**Build release:** GitHub CI emits a future *verified* signed webhook, router creates a release proposal, a human approves sharing, HERMES posts a release card. No remote `git push` or executable build is launched from Discord by default.

## Documentation links

- Discord apps/interaction model: https://docs.discord.com/developers/platform/interactions
- Discord bot data access: https://support.discord.com/hc/en-us/articles/7933951485975-Visibility-of-Bot-Data-Access
- Discord developer policy: https://support-dev.discord.com/hc/en-us/articles/8563934450327-Discord-Developer-Policy
- SeshTunes: https://discord.com/discovery/applications/1241477316891250789
- Vocard: https://discord.com/discovery/applications/605618911471468554
- GEEK Music: https://discord.com/discovery/applications/971868710237274174
- Sortr: https://discord.com/discovery/applications/1550869208768708758
- Home Assistant Discord outgoing notifications: https://www.home-assistant.io/integrations/discord/
- n8n / Discord / Home Assistant: https://n8n.io/integrations/discord/and/home-assistant/
- Spotify Listen Along: https://support.discord.com/hc/en-us/articles/115003966072-Listening-Along-with-Spotify
