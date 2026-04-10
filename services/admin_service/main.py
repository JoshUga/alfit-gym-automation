"""Admin Service - Admin dashboard, audit logging, and system health monitoring."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from shared.health import create_health_router
from shared.exceptions import AlfitException, alfit_exception_handler
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
          .wrap {{ max-width: 1100px; margin: 0 auto; padding: 24px; }}
          .card {{ border:1px solid #1e293b; border-radius:12px; background:#111827; padding:16px; margin-bottom:16px; }}
          input,button {{ border-radius:8px; border:1px solid #334155; background:#0f172a; color:#e2e8f0; padding:10px 12px; }}
          button {{ cursor:pointer; background:#22d3ee; color:#0f172a; font-weight:700; border:none; }}
          table {{ width:100%; border-collapse:collapse; }}
          th,td {{ text-align:left; padding:8px; border-bottom:1px solid #1e293b; font-size:14px; }}
          .stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:10px; }}
        </style>
      </head>
      <body>
        <div class="wrap">
          <h1>Service Admin Dashboard</h1>
          <p>Standalone admin-service dashboard.</p>
          <div class="card">
            <input id="username" placeholder="Username" value="{default_user}" />
            <input id="password" placeholder="Password" type="password" />
            <button onclick="login()">Login</button>
            <span id="msg"></span>
          </div>
          <div class="card"><div id="stats" class="stats"></div></div>
          <div class="card"><button onclick="backup()">Create Backup</button><div id="backups"></div></div>
          <div class="card"><table><thead><tr><th>Gym</th><th>Email</th><th>Members</th><th>Status</th></tr></thead><tbody id="gyms"></tbody></table></div>
        </div>
        <script>
          let headers = null;
          function setMsg(t) {{ document.getElementById('msg').textContent = t; }}
          async function api(path, opts={{}}) {{
            const r = await fetch(path, {{...opts, headers: {{'Content-Type':'application/json', ...(headers||{{}}), ...(opts.headers||{{}})}}}});
            return r.json();
          }}
          async function login() {{
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const res = await api('/api/v1/admin/service/login', {{method:'POST', body: JSON.stringify({{username,password}})}});
            if (!res?.data?.authenticated) {{ setMsg('Invalid credentials'); return; }}
            headers = {{'X-Admin-Username': username, 'X-Admin-Password': password}};
            setMsg('Authenticated');
            await load();
          }}
          async function load() {{
            const overview = await api('/api/v1/admin/service/overview');
            const gyms = await api('/api/v1/admin/service/gyms');
            const backups = await api('/api/v1/admin/service/backups');
            const stats = overview?.data || {{}};
            document.getElementById('stats').innerHTML = Object.entries(stats).map(([k,v]) => `<div class="card"><div>${{k}}</div><h3>${{v}}</h3></div>`).join('');
            document.getElementById('gyms').innerHTML = (gyms?.data || []).map(g => `<tr><td>${{g.name}}</td><td>${{g.email||'-'}}</td><td>${{g.member_count}}</td><td>${{g.is_active?'Active':'Inactive'}}</td></tr>`).join('');
            document.getElementById('backups').innerHTML = (backups?.data || []).map(b => `<div>#${{b.id}} ${{b.label||''}} <button onclick="restore(${{b.id}})">Restore</button></div>`).join('');
          }}
          async function backup() {{
            await api('/api/v1/admin/service/backups', {{method:'POST', body: JSON.stringify({{label: 'manual-ui-backup'}})}});
            await load();
          }}
          async function restore(id) {{
            await api(`/api/v1/admin/service/backups/${{id}}/restore`, {{method:'POST', body: JSON.stringify({{clear_existing:false}})}});
            await load();
          }}
        </script>
      </body>
    </html>
    """
