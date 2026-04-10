"""Admin Service - Admin dashboard, audit logging, and system health monitoring."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from shared.health import create_health_router
from shared.exceptions import AlfitException, alfit_exception_handler
from shared.database import Base, get_engine
from services.admin_service import models  # noqa: F401
from services.admin_service.routes import router as admin_router

app = FastAPI(title="Alfit Admin Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AlfitException, alfit_exception_handler)
app.include_router(create_health_router("admin-service"))
app.include_router(admin_router, prefix="/api/v1", tags=["Admin"])


@app.on_event("startup")
def create_tables() -> None:
  """Create admin service tables if they do not exist."""
  Base.metadata.create_all(bind=get_engine())


@app.get("/admin/service/dashboard", response_class=HTMLResponse)
def service_dashboard():
    default_user = os.getenv("SERVICE_ADMIN_USERNAME", "service-admin")
    return f"""
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Service Admin Dashboard</title>
        <style>
          body {{ font-family: Inter, system-ui, sans-serif; background:#0b1220; color:#e2e8f0; margin:0; }}
          .wrap {{ max-width: 1240px; margin: 0 auto; padding: 24px; }}
          .card {{ border:1px solid #1e293b; border-radius:12px; background:#111827; padding:16px; margin-bottom:16px; }}
          .row {{ display:flex; gap:8px; flex-wrap:wrap; align-items:center; }}
          input,button,label {{ border-radius:8px; border:1px solid #334155; background:#0f172a; color:#e2e8f0; padding:10px 12px; }}
          input[type='checkbox'] {{ width:16px; height:16px; vertical-align:middle; }}
          button {{ cursor:pointer; background:#22d3ee; color:#0f172a; font-weight:700; border:none; }}
          .danger {{ background:#ef4444; color:#fff; }}
          .muted {{ color:#94a3b8; font-size:13px; }}
          table {{ width:100%; border-collapse:collapse; }}
          th,td {{ text-align:left; padding:8px; border-bottom:1px solid #1e293b; font-size:14px; }}
          .stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:10px; }}
          .scroll {{ max-height:380px; overflow:auto; }}
        </style>
      </head>
      <body>
        <div class="wrap">
          <h1>Service Admin Dashboard</h1>
          <p>Operational dashboard for service-level administration.</p>
          <div class="card">
            <div class="row">
              <input id="username" placeholder="Username" value="{default_user}" />
              <input id="password" placeholder="Password" type="password" />
              <button onclick="login()">Login</button>
              <button onclick="load()">Refresh</button>
            </div>
            <span id="msg"></span>
          </div>
          <div class="card"><div id="stats" class="stats"></div></div>
          <div class="card">
            <div class="row">
              <input id="backup-label" placeholder="Backup label (optional)" />
              <button onclick="backup()">Create Backup</button>
              <label><input id="purge-backups" type="checkbox" /> Include backups in purge</label>
              <label><input id="purge-confirm" type="checkbox" /> I understand purge is destructive</label>
              <button class="danger" onclick="purgeData()">Delete All Managed Data</button>
            </div>
            <div class="muted">Tip: create a backup before purge so you can restore later.</div>
            <div id="backups" class="scroll"></div>
          </div>
          <div class="card">
            <div class="row">
              <input id="gym-filter" placeholder="Filter gyms by name/email" oninput="renderGyms()" />
              <span id="gym-summary" class="muted"></span>
            </div>
            <div class="scroll">
              <table aria-label="Gyms list"><caption>Registered gyms</caption><thead><tr><th>ID</th><th>Gym</th><th>Email</th><th>Phone</th><th>Members</th><th>Status</th></tr></thead><tbody id="gyms"></tbody></table>
            </div>
          </div>
        </div>
        <script>
          let headers = null;
          let allGyms = [];
          const esc = (v) => {{
            const node = document.createElement('span');
            node.textContent = String(v ?? '');
            return node.innerHTML;
          }};
          function setMsg(t) {{ document.getElementById('msg').textContent = t; }}
          async function api(path, opts={{}}) {{
            const r = await fetch(path, {{...opts, headers: {{'Content-Type':'application/json', ...(headers||{{}}), ...(opts.headers||{{}})}}}});
            const raw = await r.text();
            let payload = null;
            try {{
              payload = raw ? JSON.parse(raw) : null;
            }} catch {{
              payload = null;
            }}
            if (!r.ok || payload?.success === false) {{
              const textMsg = (raw || '').slice(0, 220).trim();
              throw new Error(payload?.message || textMsg || `Request failed (${{r.status}})`);
            }}
            return payload || {{ success: true, data: null }};
          }}
          async function login() {{
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            try {{
              const res = await api('/api/v1/admin/service/login', {{method:'POST', body: JSON.stringify({{username,password}})}});
              if (!res?.data?.authenticated) {{ setMsg('Invalid credentials'); return; }}
              headers = {{'X-Admin-Username': username, 'X-Admin-Password': password}};
              setMsg('Authenticated');
              await load();
            }} catch (e) {{
              setMsg(e.message);
            }}
          }}
          function renderGyms() {{
            const filter = (document.getElementById('gym-filter').value || '').toLowerCase().trim();
            const visible = allGyms.filter(g => !filter || `${{g.name||''}} ${{g.email||''}}`.toLowerCase().includes(filter));
            document.getElementById('gym-summary').textContent = `${{visible.length}} gym(s) shown`;
            document.getElementById('gyms').innerHTML = visible.map(g => `<tr><td>${{esc(g.id)}}</td><td>${{esc(g.name||'-')}}</td><td>${{esc(g.email||'-')}}</td><td>${{esc(g.phone||'-')}}</td><td>${{esc(g.member_count||0)}}</td><td>${{g.is_active?'Active':'Inactive'}}</td></tr>`).join('');
          }}
          async function load() {{
            if (!headers) {{ setMsg('Login first'); return; }}
            try {{
              const [overview, gyms, backups] = await Promise.all([
                api('/api/v1/admin/service/overview'),
                api('/api/v1/admin/service/gyms'),
                api('/api/v1/admin/service/backups')
              ]);
              const stats = overview?.data || {{}};
              document.getElementById('stats').innerHTML = Object.entries(stats).map(([k,v]) => `<div class="card"><div class="muted">${{k.replaceAll('_',' ')}}</div><h3>${{v}}</h3></div>`).join('');
              allGyms = gyms?.data || [];
              renderGyms();
              document.getElementById('backups').innerHTML = (backups?.data || []).map(b => `
                <div class="row" style="margin:6px 0">
                  <span>#${{esc(b.id)}}</span>
                  <span>${{esc(b.label||'no-label')}}</span>
                  <span class="muted">${{esc(b.created_at||'')}}</span>
                  <label><input type="checkbox" id="restore-clear-${{b.id}}" /> clear existing</label>
                  <button onclick="restore(${{b.id}})">Restore</button>
                </div>
              `).join('') || '<div class="muted">No backups yet.</div>';
              setMsg(`Loaded ${{allGyms.length}} gyms`);
            }} catch (e) {{
              setMsg(e.message);
            }}
          }}
          async function backup() {{
            const label = document.getElementById('backup-label').value || 'manual-ui-backup';
            try {{
              await api('/api/v1/admin/service/backups', {{method:'POST', body: JSON.stringify({{label}})}});
              setMsg('Backup created');
              await load();
            }} catch (e) {{
              setMsg(e.message);
            }}
          }}
          async function restore(id) {{
            const clearExisting = !!document.getElementById(`restore-clear-${{id}}`)?.checked;
            try {{
              await api(`/api/v1/admin/service/backups/${{id}}/restore`, {{method:'POST', body: JSON.stringify({{clear_existing: clearExisting}})}});
              setMsg(`Backup #${{id}} restored`);
              await load();
            }} catch (e) {{
              setMsg(e.message);
            }}
          }}
          async function purgeData() {{
            if (!document.getElementById('purge-confirm').checked) {{
              setMsg('Please confirm destructive purge first');
              return;
            }}
            const includeBackups = !!document.getElementById('purge-backups').checked;
            try {{
              const res = await api('/api/v1/admin/service/data/purge', {{method:'POST', body: JSON.stringify({{include_backups: includeBackups}})}});
              setMsg(`Purged tables: ${{res?.data?.cleared_tables || 0}}`);
              await load();
            }} catch (e) {{
              setMsg(e.message);
            }}
          }}
        </script>
      </body>
    </html>
    """
