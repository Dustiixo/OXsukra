"""HERMES-like narrow Discord bot: authorized slash commands, no message scraping."""
import asyncio
import hashlib
from .common import MAX_CHUNK
import json
import os
import urllib.request


def run_bot():
    try:
        import discord
        from discord import app_commands
    except ImportError as exc:
        raise RuntimeError('Install optional bot dependencies: pip install -r requirements-bot.txt') from exc
    bot_token=os.environ['DISCORD_BOT_TOKEN']
    guild_id=int(os.environ['DISCORD_GUILD_ID'])
    allowed={int(v.strip()) for v in os.environ['DISCORD_ALLOWED_IDS'].split(',') if v.strip()}
    hub_url=os.environ.get('FUNNEL_HUB_URL','http://127.0.0.1:8787').rstrip('/')
    api_token=os.environ['FUNNEL_BOT_API_TOKEN']
    if not allowed:
        raise RuntimeError('Set DISCORD_ALLOWED_IDS to permitted Discord user IDs')
    guild=discord.Object(id=guild_id)
    class HermesClient(discord.Client):
        async def setup_hook(self):
            await tree.sync(guild=guild)
    intents=discord.Intents.none()
    intents.guilds=True  # guild-scoped slash commands; no message-content access
    client=HermesClient(intents=intents)
    tree=app_commands.CommandTree(client)

    def call(path,method='GET',payload=None,raw=False):
        headers={'Authorization':'Bearer '+api_token}
        data=None
        if payload is not None:
            data=payload if raw else json.dumps(payload).encode()
            headers['Content-Type']='application/octet-stream' if raw else 'application/json'
        request=urllib.request.Request(hub_url+path,data=data,headers=headers,method=method)
        with urllib.request.urlopen(request,timeout=15) as r:
            return json.loads(r.read())

    async def verified(inter):
        if inter.guild_id!=guild_id or inter.user.id not in allowed:
            await inter.response.send_message('Not authorized for this workspace.',ephemeral=True)
            return False
        return True

    @tree.command(name='funnel_status',description='Shared hub health and queue overview',guild=guild)
    async def status(inter:discord.Interaction):
        if not await verified(inter):return
        await inter.response.defer(ephemeral=True)
        try:
            s=await asyncio.to_thread(call,'/api/v1/status')
            text=f"Hub: {s['items']} items, {s['notes']} notes, jobs={s['jobs']}. Google Drive mirror configured: {s['mirror_enabled']}"
        except Exception as exc:text=f'Hub unavailable: {type(exc).__name__}'
        await inter.followup.send(text[:1900],ephemeral=True)

    @tree.command(name='funnel_queue',description='Show latest intake jobs',guild=guild)
    async def queue(inter:discord.Interaction):
        if not await verified(inter):return
        await inter.response.defer(ephemeral=True)
        try:
            jobs=(await asyncio.to_thread(call,'/api/v1/jobs?limit=8'))['jobs']
            text='\n'.join(f"{j['status']}: {j['project']}/{j['name'][:70]} ({j['id'][:8]})" for j in jobs) or 'Queue empty.'
        except Exception as exc:text=f'Hub unavailable: {type(exc).__name__}'
        await inter.followup.send(text[:1900],ephemeral=True)

    @tree.command(name='funnel_find',description='Search shared items and knowledge points',guild=guild)
    @app_commands.describe(query='A file name, project keyword, or concept')
    async def find(inter:discord.Interaction,query:str):
        if not await verified(inter):return
        await inter.response.defer(ephemeral=True)
        from urllib.parse import quote
        try:
            v=await asyncio.to_thread(call,'/api/v1/search?q='+quote(query[:100]))
            lines=[f"FILE {i['project']}/{i['name']}" for i in v['items'][:8]]+[f"NOTE {n['project']}/{n['title']}" for n in v['notes'][:8]]
            text='\n'.join(lines) or 'No matches.'
        except Exception as exc:text=f'Hub unavailable: {type(exc).__name__}'
        await inter.followup.send(text[:1900],ephemeral=True)

    @tree.command(name='funnel_note',description='Create a proposed shared knowledge note',guild=guild)
    @app_commands.describe(title='Short discovery title',body='Claim or evidence (not a verified conclusion)',project='Project slug')
    async def note(inter:discord.Interaction,title:str,body:str,project:str='shared'):
        if not await verified(inter):return
        await inter.response.defer(ephemeral=True)
        try:
            v=await asyncio.to_thread(call,'/api/v1/notes','POST',{'title':title,'body':body,'project':project})
            text='Proposed note saved: '+v['note_id']
        except Exception as exc:text=f'Could not create note: {type(exc).__name__}'
        await inter.followup.send(text[:1900],ephemeral=True)

    @tree.command(name='funnel_integrations',description='Inspect which HERMES integrations are implemented, manual or proposed',guild=guild)
    async def integrations(inter:discord.Interaction):
        if not await verified(inter):return
        await inter.response.defer(ephemeral=True)
        try:
            data=await asyncio.to_thread(call,'/api/v1/integrations')
            lines=[f"{m['name']}: {m['state']}" for m in data['capabilities']]
            response='Integration registry (not proof of connection):\n'+'\n'.join(lines)
        except Exception as exc: response=f'Could not read integrations: {type(exc).__name__}'
        await inter.followup.send(response[:1900],ephemeral=True)

    @tree.command(name='funnel_purpose',description='Preview where a named file belongs; never moves or uploads it',guild=guild)
    @app_commands.describe(filename='Filename to classify (metadata only)',context='Optional description of why the file matters')
    async def purpose(inter:discord.Interaction,filename:str,context:str=''):
        if not await verified(inter):return
        await inter.response.defer(ephemeral=True)
        try:
            plan=await asyncio.to_thread(call,'/api/v1/route/preview','POST',
                {'name':filename[:180],'description':context[:500],'project':'shared'})
            matched=', '.join(plan['candidate_scores'][0]['matched_terms']) if plan['candidate_scores'] else 'none'
            response=(f"Purpose: {plan['purpose']} ({plan['decision']})\n"
                      f"Why: {plan['reason']}\nMatched: {matched}\n"
                      'Preview only. No file, channel or category changed.')
        except Exception as exc:
            response=f'Could not preview purpose: {type(exc).__name__}'
        await inter.followup.send(response[:1900],ephemeral=True)

    @tree.command(name='funnel_disclosure',description='Show the current HERMES shared-data disclosure summary',guild=guild)
    async def disclosure(inter:discord.Interaction):
        if not await verified(inter):return
        await inter.response.defer(ephemeral=True)
        try:
            data=await asyncio.to_thread(call,'/api/v1/disclosure')
            response=(f"Policy {data['version']}\n"+data['collection_default']+'\n'+
                      data['visibility']+'\n'+data['retention']+'\n'+data['external_services'])
        except Exception as exc: response=f'Could not read disclosure: {type(exc).__name__}'
        await inter.followup.send(response[:1900],ephemeral=True)

    @tree.command(name='funnel_route',description='Preview HERMES workflow steps (does NOT run them)',guild=guild)
    @app_commands.describe(event_type='Which permitted event should be previewed?')
    @app_commands.choices(event_type=[
        app_commands.Choice(name='File arrived', value='artifact.received'),
        app_commands.Choice(name='Music requested', value='music.requested'),
        app_commands.Choice(name='Session planned', value='session.planned'),
        app_commands.Choice(name='Experiment proposed', value='experiment.proposed'),
        app_commands.Choice(name='Business idea submitted', value='business.idea_submitted'),
        app_commands.Choice(name='Release proposed', value='release.proposed'),
        app_commands.Choice(name='Home alert', value='home.alert'),
    ])
    async def route(inter:discord.Interaction,event_type:app_commands.Choice[str]):
        if not await verified(inter):return
        await inter.response.defer(ephemeral=True)
        try:
            plan=await asyncio.to_thread(call,'/api/v1/automation/preview','POST',{'event_type':event_type.value})
            lines=[f"{step['action']} -> {step['adapter']} ({step['adapter_state']})" for step in plan['steps']]
            response=f"PREVIEW ONLY: {event_type.value}\n"+'\n'.join(lines)+'\nNo actions were executed.'
        except Exception as exc:response=f'Could not preview route: {type(exc).__name__}'
        await inter.followup.send(response[:1900],ephemeral=True)

    @tree.command(name='funnel_ingest',description='Archive a Discord attachment into the shared processing queue',guild=guild)
    @app_commands.describe(file='Select a file already uploaded to Discord',project='Shared project slug')
    async def ingest(inter:discord.Interaction,file:discord.Attachment,project:str='shared'):
        if not await verified(inter):return
        await inter.response.defer(ephemeral=True)
        if file.size>25*1024*1024:
            return await inter.followup.send('Use the local Funnel client for files larger than 25 MiB.',ephemeral=True)
        try:
            payload=await file.read()
            if len(payload)!=file.size:
                raise ValueError('Incomplete Discord attachment read')
            digest=hashlib.sha256(payload).hexdigest()
            session=await asyncio.to_thread(call,'/api/v1/uploads','POST',{
                'name':file.filename,'size':len(payload),'sha256':digest,'project':project,
                'annotation':f'Explicit Discord attachment capture by user {inter.user.id}'})
            ident=session['upload_id']
            for pos in range(0,len(payload),MAX_CHUNK):
                await asyncio.to_thread(call,f'/api/v1/uploads/{ident}/chunk?offset={pos}',
                                        'PATCH',payload[pos:pos+MAX_CHUNK],True)
            completed=await asyncio.to_thread(call,f'/api/v1/uploads/{ident}/complete','POST',{})
            text=f"Intake queued: {file.filename} / item {completed['item_id']} / job {completed['job_id']}"
        except Exception as exc:
            text=f'Attachment intake failed: {type(exc).__name__}: {str(exc)[:200]}'
        await inter.followup.send(text[:1900],ephemeral=True)

    @client.event
    async def on_ready():
        print(f'HERMES online as {client.user}; guild {guild_id}',flush=True)

    client.run(bot_token,log_handler=None)
