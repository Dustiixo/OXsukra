# Discord blueprint: clubhouse first, computing second

These are **proposed names**, to be restyled using the look, emoji language and memes from existing servers. Implement by hand in a test server after the group agrees. A JSON reference lives in `server_blueprint.json`; it does **not** automatically create Discord channels.

| Category | Text/forum channels | Voice and intent |
|---|---|---|
| 00 // ENTRY | `#start-here`, `#disclosure-and-rules`, `#announcements` | Start with disclosure and who operates things |
| 01 // BACK ALLEY | `#general`, `#memes`, `#clip-dump` | `The Garage`, `AFK`; casual talk stays casual |
| 02 // DUMP HUB | `#file-drop`, `#intake-status`, `#research-links` | Discord-native small uploads; larger files via local app |
| 03 // ENGINE ROOM | `#dev-general`, `#ixo`, `#syntra`, `#apc-odin`, `#cross-project` | `Dev Lab`, `Screen Share`; project discussions |
| 04 // ALCHEMY | `#experiments`, `#comparisons`, `#verification` | Explicit proposed intelligence experiments, evidence links |
| 05 // BUSINESS INTENTIONS | `#concepts-only`, `#opportunities` | **No sensitive deal data on current shared hub** |
| 06 // MEMORY | `#eureka`, `#decisions`, `#knowledge-index` | Proposed knowledge, approved decisions, backlinks |
| 07 // LIVE | `#stream-schedule`, `#music-requests`, `#showcase` | `Listening Room`, `Live Studio`; licensed playback bots only |
| 08 // CONTROL | `#hermes-status`, `#bot-requests`, `#incident-notices` | Only operators post integration notices where suitable |

## Roles

- `@everyone`: only the channels appropriate for ordinary members; no management permissions.
- `@Member`: standard chat/voice access. **Not** implied permission to archive or publish somebody else's files.
- `@ProjectOwner`: a *discussion* role, not implemented as hub-level ACL yet.
- `@HubOperator`: human infrastructure steward, scoped to private operational channels.
- `@BotManager`: reviews app additions and minimum permissions; does not get arbitrary admin by default.
- `@HERMES`: separate bot identity, slash commands, ability to reply, optionally a webhook to `#hermes-status`.

## Existing bots to consider, separately

1. **Music bot** for social voice rooms and permitted sources. Do not assume every bot permits programmatic queue control or that all streamed tracks are licensed.
2. **Discord AutoMod** for ordinary moderation; don't reinvent it in HERMES.
3. **Events/scheduling bot** for calls, builds and listening sessions.
4. **Poll/voting bot** for collaborative approvals; crucial decisions should be recorded with who decided and what was approved.
5. **GitHub notifications** through an officially supported integration or narrowly scoped webhook.
6. **HERMES** for project-specific queue/search/capture/disclosure status, not spying on regular chat.

Never grant bots Administrator by default. Review each app's permissions, privacy policy, data retention and developer. The **HERMES bot is optional** until the guild is ready and the operator completes the setup.

## Discord template caveat

Discord server templates copy categories, ordinary channels, roles and permissions but do not copy chat history, bots or all Community channel types. We cannot generate an actual Discord server-template URL from this offline package. Once the test server is created and approved, a member with Manage Server can generate a template from Discord desktop/browser.

**Docs:** https://support.discord.com/hc/en-us/articles/360041033511-Server-Templates
