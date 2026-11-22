# Proposal: our own Discord-backed development clubhouse

**For:** four collaborating developers (IXO, Syntra, APC/Odin and shared experiments)  
**Project:** OX Funnel + HERMES Bridge  
**Decision requested:** approve a small, private 4-person pilot. **Not** approve full data access, a joint company, a shared license, or autonomous code execution.

## Why bother?

Our best work may begin during a chaotic voice chat, a screen-share, a game, a clip, a broken build or an absurd joke. Today the useful artifact disappears inside chat history or a private drive. We need a common, controllable route from *conversation* to *evidence* to *usable artifact* while keeping each developer's machines and projects independent.

## The deliberately simple model

- **Discord is the social room.** Hang out, stream, play music through a separately approved bot, share memes, discuss designs. Normal chat and voice are not silently archived.
- **Funnel is the front door for data.** Use Discord's default upload for ordinary attachments. For large or reusable items, drag into the local app or explicitly opt into a watched drop folder.
- **Hub is the ledger and routing station.** It receives chunks, verifies SHA-256, queues safe inspection, labels ownership, serves a clickable dashboard/API and can mirror to an approved storage destination.
- **HERMES is the messenger.** Its optional Discord bot reports, searches, accepts selected attachments and receives approved commands. It is not a super-admin and doesn't control all other bots.
- **Knowledge is not ownership.** Approved summaries can export to Obsidian; source code lives in its proper repository. A discovery remains a proposal until a developer verifies it.

## Shared channels, independent projects

Project areas can cover IXO, Syntra, APC/Odin, shared intelligence experiments, Dump Hub, streaming/music, open research, and *Business Intentions*. Restricted business information stays outside this prototype until actual access controls are built and tested.

## Pilot demonstration (what we'll actually do)

1. Agree the disclosure and appoint one hub operator.
2. Start the hub on one private machine. Three other developers use the sender after receiving individual tokens privately.
3. Each uploads a **dummy** sample file. Confirm identity, checksum, search, and processing status in the dashboard.
4. Make one proposed knowledge note and export Markdown for Obsidian.
5. Optionally connect a staging Discord bot in a test server and verify only approved slash commands work.
6. Review failures, retention, ownership and access before enabling a real Google Drive mirror.

## What we are explicitly NOT agreeing to

No automatic archival of conversations; no recording voice/streams; no general remote shell; no uploading entire local drives; no autonomous execution of code; no transfer of intellectual property; no public release; no business venture or shared credentials by implication.

## Proposed decisions at the meeting

- Do we want the pilot? (Yes / revise / no)
- Which machine or VPS is the hub? Who pays/operates it?
- Who owns infrastructure, who approves access, and who can stop the service?
- What shared files are okay for the first pilot? What stays private?
- Which bot is first: HERMES slash commands, a standalone music bot, or both?
- What are the two observable success criteria and the abort conditions?

**Suggested success gate:** four real developer clients can upload small consenting test artifacts to one private hub, verify contents and ownership, search the index, and export knowledge, without any upload happening without a member's action. This must pass before remote worker automation.

## Roles without hierarchy over creative work

- **Server steward:** maintains Discord channels and bot permissions.
- **Hub operator:** manages vault, backups, tokens, incident response and uptime.
- **Adapters reviewers:** evaluate integrations and test permissions.
- **Project owners:** approve whether their own work enters the shared archive and its license/use.

These are operational responsibilities, not an IP ownership assignment. They may rotate or be shared.
