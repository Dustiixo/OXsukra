"""HERMES control-plane schema: inspectable manifests and safe routing previews.

A manifest is NOT an installed plugin. A route preview is NOT execution.
No uploaded payload, user message, audio, or third-party bot is forwarded here.
"""
from __future__ import annotations

from dataclasses import dataclass

DISCLOSURE_VERSION = 'HERMES-DISCLOSURE-0.2'

# Preconfigured capabilities are distinguished from documented external options.
CAPABILITIES = (
    {'id':'funnel_hub', 'category':'core', 'name':'OX Funnel Hub',
     'state':'implemented', 'interface':'authenticated HTTP API',
     'data':'submitted artifact metadata and approved knowledge',
     'restriction':'v0.2 has one shared workspace; no project-level isolation'},
    {'id':'hermes_discord', 'category':'chat', 'name':'HERMES Discord bot',
     'state':'adapter_included_not_live', 'interface':'slash commands and Discord attachment upload',
     'data':'explicit command inputs and selected attachments',
     'restriction':'requires guild/user allowlist and credentials; no automatic chat harvesting'},
    {'id':'discord_music', 'category':'music', 'name':'Third-party music bot',
     'state':'external_manual', 'interface':'Discord App Directory / voice channel',
     'data':'queue and song requests handled by the selected third-party provider',
     'restriction':'no known third-party API is assumed; check licensing and bot permissions'},
    {'id':'team_music', 'category':'music', 'name':'Team-owned audio playback adapter',
     'state':'proposed', 'interface':'future licensed playback worker',
     'data':'audio the team owns or is licensed to use',
     'restriction':'no playback service implemented; do not bypass provider access controls'},
    {'id':'google_drive', 'category':'storage', 'name':'Shared Google Drive',
     'state':'optional_adapter_included', 'interface':'rclone mirror after verified upload',
     'data':'verified artifact blobs selected for the shared destination',
     'restriction':'requires configured remote; actual cloud transfer untested'},
    {'id':'obsidian', 'category':'knowledge', 'name':'Obsidian vault',
     'state':'export_implemented', 'interface':'Markdown ZIP export',
     'data':'approved-to-share notes, currently proposed by default',
     'restriction':'no live two-way sync or permission enforcement per project'},
    {'id':'local_llm', 'category':'intelligence', 'name':'Local Ollama',
     'state':'optional_client_included', 'interface':'localhost HTTP on each member machine',
     'data':'user-requested annotations and selected shared knowledge',
     'restriction':'not a server-wide inference farm; human verification required'},
    {'id':'intelligence_alchemy', 'category':'intelligence', 'name':'Intelligence Alchemy',
     'state':'proposed', 'interface':'future model-comparison jobs',
     'data':'explicitly selected experiment inputs and evidence',
     'restriction':'never auto-train on Discord API data or auto-approve model conclusions'},
    {'id':'business_intentions', 'category':'business', 'name':'Business Intentions',
     'state':'proposed_private', 'interface':'future restricted approval workflow',
     'data':'commercial proposals, budgets and IP records',
     'restriction':'DO NOT place sensitive business material on shared v0.2 hub'},
    {'id':'github', 'category':'development', 'name':'GitHub',
     'state':'proposed', 'interface':'future authorized GitHub App/webhook',
     'data':'selected issue/release metadata and reference links',
     'restriction':'no repository writes implemented'},
    {'id':'n8n', 'category':'automation', 'name':'n8n workflows',
     'state':'proposed', 'interface':'future restricted internal HTTPS webhook',
     'data':'small purpose-limited job payloads',
     'restriction':'never accept arbitrary command execution from Discord'},
    {'id':'home_assistant', 'category':'automation', 'name':'Home Assistant',
     'state':'external_manual', 'interface':'optional outbound Discord notifications',
     'data':'user-selected device alerts',
     'restriction':'official Home Assistant Discord integration only sends notifications'},
    {'id':'events_tickets', 'category':'community', 'name':'Events / ticket bots',
     'state':'external_manual', 'interface':'third-party app independently authorized',
     'data':'event RSVP or ticket details under provider policy',
     'restriction':'not readable by HERMES unless an explicit integration is provided'},
    {'id':'moderation', 'category':'community', 'name':'Discord AutoMod / moderation bot',
     'state':'external_manual', 'interface':'Discord-native or third-party moderation',
     'data':'moderation metadata subject to provider policy',
     'restriction':'separate from shared knowledge automation'},
)

# A workflow describes a possible route; it does not create or run a job.
RECIPES = {
    'artifact.received': (
        ('verify_artifact','funnel_hub',False),
        ('index_safe_metadata','funnel_hub',False),
        ('notify_upload','hermes_discord',True),
        ('mirror_file','google_drive',True),
    ),
    'music.requested': (
        ('open_music_request','discord_music',True),
        ('record_optional_playlist_reference','funnel_hub',True),
    ),
    'session.planned': (
        ('propose_event','events_tickets',True),
        ('post_session_notice','hermes_discord',True),
    ),
    'experiment.proposed': (
        ('create_unverified_knowledge_note','obsidian',True),
        ('queue_model_comparison','intelligence_alchemy',True),
    ),
    'business.idea_submitted': (
        ('request_private_business_review','business_intentions',True),
    ),
    'home.alert': (
        ('notify_discord_channel','home_assistant',True),
    ),
    'release.proposed': (
        ('request_code_review','github',True),
        ('announce_release_candidate','hermes_discord',True),
    ),
}

DISCLOSURE = {
    'version': DISCLOSURE_VERSION,
    'purpose': 'Shared manual artifact intake, event tracking, proposed notes, and explicit automation previews.',
    'collection_default': 'No passive Discord conversation capture, voice recording, screen recording, or automatic file transfer.',
    'inputs': 'Files deliberately uploaded or ingested, selected command text, account label, metadata, checksums and explicit notes.',
    'storage': 'Private local/VPS vault SQLite + content-addressed blobs; optional separately configured Google Drive mirror.',
    'model_processing': 'Optional local inference on explicitly selected data; generated conclusions are unverified. No model training on Discord API data.',
    'external_services': 'Any music, moderation, ticket or event bot is a separate provider with its own terms, permissions and disclosures.',
    'visibility': 'v0.2 has shared member access without project-level ACLs; never submit confidential business or personal records yet.',
    'retention': 'No automatic purge in this prototype. Operators must specify retention and deletion before admitting real group content.',
    'approval': 'Routes are dry-run proposals. No remote action is executed by this automation interface.',
    'access': 'Member/admin Bearer credentials; private network/HTTPS necessary off localhost.',
    'rights': 'Operators must publish contact, deletion request process, and verified incident-reporting contact before deployment.',
}


def capability_catalog():
    return {'disclosure_version':DISCLOSURE_VERSION,'capabilities':[dict(x) for x in CAPABILITIES]}


def route_preview(event_type: str):
    if not isinstance(event_type,str) or event_type not in RECIPES:
        raise ValueError('Unknown event type; consult /api/v1/automation/types')
    by_id={c['id']:c for c in CAPABILITIES}
    return {
        'event_type':event_type,'disclosure_version':DISCLOSURE_VERSION,
        'executed':False,'mode':'preview_only',
        'steps':[{'action':action,'adapter':adapter,
                  'adapter_state':by_id[adapter]['state'],
                  'external_approval_required':approval,
                  'executed':False} for action,adapter,approval in RECIPES[event_type]]
    }


def event_types():
    return sorted(RECIPES)


def validate_explicit_event(data):
    if not isinstance(data,dict):
        raise ValueError('Expected JSON object')
    event_type=data.get('event_type')
    route_preview(event_type)
    if data.get('disclosure_version')!=DISCLOSURE_VERSION or data.get('acknowledged') is not True:
        raise PermissionError('Disclosure acknowledgement and current disclosure_version required')
    summary=data.get('summary','')
    if not isinstance(summary,str) or not (1<=len(summary.strip())<=300):
        raise ValueError('Summary must be between 1 and 300 characters')
    # No free-form arbitrary payload, file contents or channel-message transcript.
    if set(data)-{'event_type','project','summary','disclosure_version','acknowledged'}:
        raise ValueError('Unsupported fields; metadata-only events')
    return event_type, summary.strip()
