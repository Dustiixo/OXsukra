/* PARALLAX pure event hygiene + bounded streaming, deliberately no page/body payloads. */
(function(root) {
  "use strict";
  const ACCOUNT = /(?:^|\/)(?:login|logout|signin|sign-in|signup|sign-up|account|accounts|auth|oauth|callback|payment|checkout|billing|settings|reset|password|private|admin|session)(?:\/|$)/i;
  const SECRET_PATH = /(?:bearer|token|secret|api[_-]?key|access[_-]?key|jwt|sessionid|authorization)/i;
  function cleanUrl(raw) {
    if (typeof raw !== "string" || raw.length > 4096) return null;
    try {
      const u = new URL(raw);
      if (!["https:", "http:"].includes(u.protocol) || u.username || u.password) return null;
      const hostname = u.hostname.toLowerCase();
      if (!hostname || hostname === "localhost" || hostname.endsWith(".local") || hostname.endsWith(".internal") || hostname.endsWith(".localhost")) return null;
      // Public-site URL metadata only; prevent accidental local/intranet targeting.
      if (/^\d+\.\d+\.\d+\.\d+$/.test(hostname) || hostname.startsWith("[") || hostname.includes(":")) return null;
      if (ACCOUNT.test(u.pathname) || SECRET_PATH.test(u.pathname)) return null;
      // No query, fragment, username, password, or explicit nonstandard port in evidence.
      if (u.port && !["80", "443"].includes(u.port)) return null;
      let path = u.pathname;
      if (path.length > 180) path = path.slice(0, 180) + "…";
      // Pseudonymous opaque high-entropy segments are not retained.
      if (path.split("/").some(x => x.length > 28 || /[A-Za-z0-9_-]{20,}/.test(x))) path = "/[redacted-path]";
      return `${u.origin}${path}`;
    } catch { return null; }
  }
  function origin(raw) { const s = cleanUrl(raw); if (!s) return null; try { return new URL(s).origin; } catch { return null; } }
  function sameOrigin(a,b) { const x=origin(a),y=origin(b); return !!x && x===y; }
  const EVENT_TYPES = new Set(["navigation", "request", "response", "redirect", "popup", "link", "asset", "mutation", "resource_hint", "cookie_meta", "error", "dom_removed", "overflow"]);
  function safeEvent(incoming, armedOrigin, now=Date.now()) {
    if (!incoming || !EVENT_TYPES.has(incoming.type)) return null;
    const from = cleanUrl(incoming.from || armedOrigin);
    const to = incoming.to ? cleanUrl(incoming.to) : null;
    if (!from || !sameOrigin(from, armedOrigin)) return null;
    if (incoming.to && !to) return null;
    const event = {type:incoming.type, from, to, at:Math.floor(now), source:"observed", tabId:Number.isInteger(incoming.tabId)?incoming.tabId:null};
    const kind = String(incoming.kind || "").slice(0,32).replace(/[^a-zA-Z0-9_./-]/g, "");
    if (kind) event.kind=kind;
    if (Number.isFinite(incoming.status)) event.status=Math.max(0,Math.min(599,Math.trunc(incoming.status)));
    if (Number.isFinite(incoming.bytes)) event.bytes=Math.max(0,Math.min(1e10,Math.trunc(incoming.bytes)));
    if (Number.isFinite(incoming.count)) event.count=Math.max(1,Math.min(1e6,Math.trunc(incoming.count)));
    if (["link","asset","resource_hint","dom_removed", "overflow"].includes(incoming.type)) event.source="declared-or-timed";
    if (incoming.type === "cookie_meta") {
      event.to=null;
      event.name=String(incoming.name||"").replace(/[^a-zA-Z0-9._-]/g,"").slice(0,65);
      event.cookieDomain=String(incoming.cookieDomain||"").slice(0,128).replace(/[^a-zA-Z0-9.\-]/g,"");
      event.httpOnly=!!incoming.httpOnly; event.secure=!!incoming.secure; event.session=!!incoming.session;
      event.sameSite=["no_restriction","lax","strict","unspecified"].includes(incoming.sameSite)?incoming.sameSite:"unspecified";
    }
    return event;
  }
  class BoundedFeed {
    constructor(maxQueue=1200, maxGraph=150, maxEdges=350) {
      this.queue=[];this.graph=new Map();this.edges=new Map();this.dropped=0;this.total=0;
      this.maxQueue=maxQueue;this.maxGraph=maxGraph;this.maxEdges=maxEdges;
    }
    add(event) {
      if (!event) return;
      this.total++;
      if(event.type==="overflow")this.dropped+=event.count||1;
      const fromId=event.from;
      const toId=event.to;
      const acceptedFrom=this._node(fromId, "site");
      const acceptedTo=toId?this._node(toId, event.kind||event.type):false;
      if(toId && acceptedFrom && acceptedTo) {
        const k=`${event.type}|${fromId}|${toId}`;
        if(this.edges.has(k)) { const v=this.edges.get(k);v.count++;v.at=event.at; }
        else if(this.edges.size<this.maxEdges) this.edges.set(k,{from:fromId,to:toId,type:event.type,count:1,at:event.at,source:event.source});
        else this.dropped++;
      }
      if(this.queue.length>=this.maxQueue) {this.queue.shift();this.dropped++;}
      this.queue.push(event);
    }
    _node(id, type) {
      if(this.graph.has(id)){this.graph.get(id).hits++;return true;}
      if(this.graph.size>=this.maxGraph){this.dropped++;return false;}
      this.graph.set(id,{id,type,hits:1});return true;
    }
    take(n=48){return this.queue.splice(0,Math.min(Math.max(n,0),64));}
    snapshot(){return {nodes:[...this.graph.values()],edges:[...this.edges.values()],total:this.total,dropped:this.dropped,pending:this.queue.length};}
    reset(){this.queue=[];this.graph.clear();this.edges.clear();this.dropped=0;this.total=0;}
  }
  const api={cleanUrl,origin,sameOrigin,safeEvent,BoundedFeed};
  if(typeof module!=="undefined" && module.exports)module.exports=api;
  else root.ParallaxCore=api;
})(typeof globalThis!=="undefined"?globalThis:this);
