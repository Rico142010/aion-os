import hashlib
import hmac
import html
import json
import os
import secrets
import sqlite3
import threading
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from email.parser import BytesParser
from email.policy import default as email_policy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import billing
import youtube
import paypal

ROOT = Path(__file__).parent
def load_dotenv():
    envfile=ROOT/".env"
    if envfile.exists():
        for line in envfile.read_text(encoding="utf-8").splitlines():
            line=line.strip()
            if line and not line.startswith("#") and "=" in line:
                key,value=line.split("=",1)
                key=key.strip()
                value=value.strip().strip('"').strip("'")
                if not os.environ.get(key,"").strip():
                    os.environ[key]=value
load_dotenv()
DB = Path(os.getenv("DATABASE_PATH", ROOT / "data" / "aion.db"))
PORT = int(os.getenv("PORT", "8000"))
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai").strip() or "openai"
AI_KEY = os.getenv("AI_API_KEY", "").strip() or os.getenv("OPENAI_API_KEY", "").strip()
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://api.openai.com/v1").strip().rstrip("/")
AI_MODEL = os.getenv("AI_MODEL", "").strip() or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DB.parent.mkdir(parents=True, exist_ok=True)
SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, salt TEXT NOT NULL, password TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, expires INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS brands(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, name TEXT NOT NULL, niche TEXT DEFAULT '', voice TEXT DEFAULT '', audience TEXT DEFAULT '', created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS projects(id INTEGER PRIMARY KEY, brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE, title TEXT NOT NULL, platform TEXT DEFAULT 'YouTube', status TEXT DEFAULT 'idea', idea TEXT DEFAULT '', script TEXT DEFAULT '', storyboard TEXT DEFAULT '', seo TEXT DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS assets(id INTEGER PRIMARY KEY, brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE, name TEXT NOT NULL, kind TEXT NOT NULL, url TEXT DEFAULT '', notes TEXT DEFAULT '', created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS metrics(id INTEGER PRIMARY KEY, brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE, platform TEXT NOT NULL, label TEXT NOT NULL, views INTEGER DEFAULT 0, followers INTEGER DEFAULT 0, revenue REAL DEFAULT 0, measured_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS workflows(id INTEGER PRIMARY KEY, brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE, name TEXT NOT NULL, prompt TEXT NOT NULL, cadence TEXT DEFAULT 'manual', enabled INTEGER DEFAULT 0, last_run TEXT);
CREATE TABLE IF NOT EXISTS jobs(id INTEGER PRIMARY KEY, brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE, workflow_id INTEGER REFERENCES workflows(id) ON DELETE SET NULL, kind TEXT NOT NULL, status TEXT DEFAULT 'queued', result TEXT DEFAULT '', created_at TEXT NOT NULL, finished_at TEXT);
CREATE TABLE IF NOT EXISTS youtube_connections(brand_id INTEGER PRIMARY KEY REFERENCES brands(id) ON DELETE CASCADE, token_blob BLOB NOT NULL, channel_id TEXT NOT NULL, channel_title TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS youtube_oauth_states(state TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE, expires INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS subscriptions(user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE, provider TEXT NOT NULL, external_subscription_id TEXT UNIQUE, plan_key TEXT NOT NULL, status TEXT NOT NULL, current_period_end TEXT, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS billing_events(provider TEXT NOT NULL, event_id TEXT NOT NULL, event_type TEXT NOT NULL, processed_at TEXT NOT NULL, PRIMARY KEY(provider,event_id));
CREATE TABLE IF NOT EXISTS ai_usage(user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, period TEXT NOT NULL, ai_generations INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(user_id,period));
"""

@contextmanager
def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

with db() as conn:
    conn.executescript(SCHEMA)

def now(): return datetime.now(timezone.utc).isoformat()
def digest(pw, salt): return hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 240000).hex()

def youtube_access_token(brand_id):
    with db() as c:
        row=c.execute("SELECT token_blob FROM youtube_connections WHERE brand_id=?",(brand_id,)).fetchone()
    if not row: raise ValueError("Conecta primero un canal de YouTube.")
    credentials=youtube.unprotect(row["token_blob"])
    if int(credentials.get("expires_at",0)) < int(time.time())+120:
        refreshed=youtube.refresh(credentials["refresh_token"])
        credentials.update(refreshed)
        credentials["expires_at"]=int(time.time())+int(refreshed.get("expires_in",3600))
        with db() as c:
            c.execute("UPDATE youtube_connections SET token_blob=?,updated_at=? WHERE brand_id=?",
                      (youtube.protect(credentials),now(),brand_id))
    return credentials["access_token"]

def ai(prompt, system="You are AION STUDIO, an expert content strategist. Reply in the user's language. Be specific and do not invent current market data."):
    provider = AI_PROVIDER.strip() or "openai"
    provider_name = "OpenAI" if provider.lower() == "openai" else provider
    if not AI_KEY: raise ValueError(f"No hay una clave configurada para {provider_name}. Añade AI_API_KEY (o OPENAI_API_KEY para OpenAI) al entorno de AION STUDIO.")
    base = urlparse(AI_BASE_URL)
    if base.scheme != "https" and not (base.scheme == "http" and base.hostname in ("localhost", "127.0.0.1", "::1")):
        raise ValueError("AI_BASE_URL debe usar HTTPS; HTTP solo se permite para un proveedor local en localhost.")
    body = json.dumps({"model": AI_MODEL, "messages": [{"role":"system","content":system},{"role":"user","content":prompt}], "temperature":0.7}).encode()
    req = urllib.request.Request(AI_BASE_URL + "/chat/completions", data=body, headers={"Authorization":"Bearer "+AI_KEY,"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r: return json.loads(r.read())['choices'][0]['message']['content']
    except urllib.error.HTTPError as e:
        detail=e.read().decode(errors="replace")[:1000]
        try:
            error=json.loads(detail).get("error",{})
            code=error.get("code") or error.get("type")
        except (ValueError,AttributeError):
            code=None
        if code=="credit_balance_exhausted" and provider.lower()=="openai":
            raise ValueError("Se agotaron los créditos prepagados de la organización OpenAI asociada a esta clave. Añade créditos o revisa la facturación de API y vuelve a intentarlo: https://platform.openai.com/settings/organization/billing/.") from None
        if e.code==429 and code in ("insufficient_quota","organization_usage_limit_exceeded","organization_spend_limit_exceeded","project_spend_limit_exceeded"):
            raise ValueError(f"{provider_name} rechazó la solicitud por cuota o límite de gasto. Revisa la facturación y los límites de uso asociados a esta clave API.") from None
        if e.code==429:
            raise ValueError(f"{provider_name} aplicó un límite temporal de solicitudes. Espera un momento y vuelve a intentarlo; si persiste, revisa los límites de velocidad del proyecto.") from None
        raise ValueError(f"{provider_name} respondió {e.code}: {detail[:300]}") from None
    except urllib.error.URLError as e:
        reason=e.reason
        provider_host=urlparse(AI_BASE_URL).hostname or "el proveedor configurado"
        if getattr(reason,"winerror",None)==10013 or "WinError 10013" in str(reason):
            raise ValueError(f"Windows bloqueó la conexión saliente a {provider_host}:443 (WinError 10013). Permite HTTPS saliente para el proceso de Python/AION o ejecuta el servidor en un entorno con acceso de red.") from None
        raise ValueError(f"No se pudo conectar con {provider_name}: {reason}") from None

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): print(f"{self.address_string()} - {fmt % args}")
    def redirect(self, location):
        self.send_response(302); self.send_header("Location",location); self.send_header("Cache-Control","no-store"); self.end_headers()
    def send(self, status, data, content_type="application/json; charset=utf-8"):
        raw = data if isinstance(data, bytes) else (json.dumps(data, ensure_ascii=False).encode() if content_type.startswith("application/json") else data.encode())
        self.send_response(status); self.send_header("Content-Type",content_type); self.send_header("Content-Length",str(len(raw))); self.send_header("X-Content-Type-Options","nosniff"); self.send_header("Content-Security-Policy","default-src 'self'; connect-src 'self' https://www.paypal.com https://api-m.sandbox.paypal.com https://api-m.paypal.com; style-src 'self' 'unsafe-inline' https://www.paypal.com; script-src 'self' https://www.paypal.com; frame-src https://www.paypal.com https://www.sandbox.paypal.com; img-src 'self' data: https:"); self.end_headers(); self.wfile.write(raw)
    def body(self):
        n=int(self.headers.get("Content-Length",0)); return json.loads(self.rfile.read(n) or b"{}")
    def user(self):
        token=self.headers.get("Cookie","").replace("aion_session=","").split(";",1)[0]
        with db() as c: row=c.execute("SELECT user_id FROM sessions WHERE token=? AND expires>?",(token,int(time.time()))).fetchone()
        return row[0] if row else None
    def auth(self):
        u=self.user()
        if not u: self.send(401,{"error":"Inicia sesión para continuar."}); return None
        return u
    def youtube_callback(self):
        query=parse_qs(urlparse(self.path).query)
        state=query.get("state",[""])[0]
        if query.get("error"):
            return self.youtube_callback_error("Google canceló o rechazó la autorización. Vuelve a AION y pulsa Conectar YouTube para iniciar un intento nuevo.")
        code=query.get("code",[""])[0]
        if not state or not code:
            return self.youtube_callback_error("Esta dirección es el retorno de OAuth y no se debe abrir directamente. Inicia la conexión desde AION Studio para que Google incluya el código de autorización.")
        with db() as c:
            saved=c.execute("SELECT * FROM youtube_oauth_states WHERE state=? AND expires>?",(state,int(time.time()))).fetchone()
            if saved:c.execute("DELETE FROM youtube_oauth_states WHERE state=?",(state,))
        if not saved:return self.youtube_callback_error("La autorización caducó o no corresponde a esta sesión. Vuelve a AION y conecta YouTube de nuevo.")
        try:
            credentials=youtube.exchange_code(code)
            if not credentials.get("refresh_token"):
                raise ValueError("Google no entregó un refresh token. Revoca el acceso de AION en tu cuenta Google y vuelve a conectar.")
            credentials["expires_at"]=int(time.time())+int(credentials.get("expires_in",3600))
            channel=youtube.channel(credentials["access_token"])
            with db() as c:
                c.execute("INSERT INTO youtube_connections(brand_id,token_blob,channel_id,channel_title,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(brand_id) DO UPDATE SET token_blob=excluded.token_blob,channel_id=excluded.channel_id,channel_title=excluded.channel_title,updated_at=excluded.updated_at",
                          (saved["brand_id"],youtube.protect(credentials),channel["id"],channel["title"],now()))
            return self.redirect("/?youtube=connected")
        except Exception as exc:
            return self.youtube_callback_error("No se pudo terminar la conexión con YouTube: " + str(exc), status=502)
    def youtube_callback_error(self, message, status=400):
        page = """<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Conexión de YouTube · AION Studio</title><body style="margin:0;background:#0b1020;color:#edf1ff;font:16px system-ui;min-height:100vh;display:grid;place-items:center"><main style="max-width:560px;margin:24px;padding:32px;border:1px solid #29324a;border-radius:18px;background:#11182b"><p style="color:#8da6ff;font-weight:700">AION STUDIO · YOUTUBE</p><h1 style="font-size:25px">No se completó la conexión</h1><p>""" + html.escape(message) + """</p><p>Abre AION, inicia sesión y usa <b>Integraciones → Conectar YouTube</b>. No copies ni compartas la dirección de retorno.</p><p>Si Google muestra un error de redirección, confirma que la URI autorizada sea exactamente:<br><code>http://localhost:8000/api/integrations/youtube/callback</code></p><a style="display:inline-block;margin-top:12px;padding:12px 18px;border-radius:10px;background:#7d8cff;color:#081024;text-decoration:none;font-weight:700" href="/">Volver a AION Studio</a></main></body></html>"""
        return self.send(status,page,"text/html; charset=utf-8")
    def do_GET(self):
        path=urlparse(self.path).path
        if path=="/" or path=="/index.html": return self.send(200,(ROOT/"static"/"index.html").read_bytes(),"text/html; charset=utf-8")
        if path in ("/app.js","/styles.css"): return self.send(200,(ROOT/"static"/path.lstrip("/")).read_bytes(),"text/javascript; charset=utf-8" if path.endswith(".js") else "text/css; charset=utf-8")
        if path=="/api/health": return self.send(200,{"ok":True,"database":"sqlite","aiConfigured":bool(AI_KEY),"youtubeConfigured":youtube.configured()})
        if path=="/api/plans": return self.send(200,billing.public_plans())
        if path=="/api/billing/config": return self.send(200,paypal.public_config())
        if path=="/api/integrations/youtube/callback": return self.youtube_callback()
        u=self.auth()
        if not u:return
        with db() as c:
            if path=="/api/me": return self.send(200,{"id":u,"email":c.execute("SELECT email FROM users WHERE id=?",(u,)).fetchone()[0],"aiConfigured":bool(AI_KEY),"billing":billing.snapshot(c,u),"plans":billing.public_plans()})
            if path=="/api/brands": return self.send(200,[dict(x) for x in c.execute("SELECT * FROM brands WHERE user_id=? ORDER BY id DESC",(u,))])
            if path.startswith("/api/brand/"):
                try: bid=int(path.split("/")[3])
                except: return self.send(400,{"error":"ID inválido"})
                b=c.execute("SELECT * FROM brands WHERE id=? AND user_id=?",(bid,u)).fetchone()
                if not b:return self.send(404,{"error":"Marca no encontrada"})
                base={"brand":dict(b)}
                for table in ("projects","assets","metrics","workflows","jobs"):
                    base[table]=[dict(x) for x in c.execute(f"SELECT * FROM {table} WHERE brand_id=? ORDER BY id DESC",(bid,))]
                yt=c.execute("SELECT channel_id,channel_title,updated_at FROM youtube_connections WHERE brand_id=?",(bid,)).fetchone()
                base["youtube"]={"connected":bool(yt),"configured":youtube.configured(),**(dict(yt) if yt else {})}
                bits=path.split("/"); action="/".join(bits[4:]) if len(bits)>4 else ""
                if action=="youtube/connect":
                    if not youtube.configured():return self.send(503,{"error":"Añade YOUTUBE_CLIENT_ID y YOUTUBE_CLIENT_SECRET en .env y reinicia AION STUDIO."})
                    state=secrets.token_urlsafe(32)
                    c.execute("DELETE FROM youtube_oauth_states WHERE expires<?",(int(time.time()),))
                    c.execute("INSERT INTO youtube_oauth_states(state,user_id,brand_id,expires) VALUES(?,?,?,?)",(state,u,bid,int(time.time())+600))
                    return self.redirect(youtube.authorization_url(state))
                if action=="youtube/status":return self.send(200,base["youtube"])
                if action=="youtube/metrics":
                    try:
                        token=youtube_access_token(bid)
                        end=(datetime.now(timezone.utc).date()-timedelta(days=1)).isoformat()
                        start=(datetime.now(timezone.utc).date()-timedelta(days=29)).isoformat()
                        channel=youtube.channel(token); report=youtube.analytics(token,start,end)
                        return self.send(200,{"channel":channel,"startDate":start,"endDate":end,"report":report})
                    except Exception as exc:return self.send(502,{"error":str(exc)})
                return self.send(200,base)
        return self.send(404,{"error":"Ruta no encontrada"})
    def youtube_publish(self,path):
        u=self.auth()
        if not u:return
        bits=path.split("/")
        try:bid=int(bits[3])
        except:return self.send(400,{"error":"ID de marca inválido"})
        with db() as c:
            if not c.execute("SELECT id FROM brands WHERE id=? AND user_id=?",(bid,u)).fetchone():return self.send(404,{"error":"Marca no encontrada"})
            if not c.execute("SELECT 1 FROM youtube_connections WHERE brand_id=?",(bid,)).fetchone():return self.send(409,{"error":"Conecta primero tu canal de YouTube."})
        content_type=self.headers.get("Content-Type","")
        if not content_type.lower().startswith("multipart/form-data;"):
            return self.send(415,{"error":"Se esperaba un formulario multipart con el vídeo."})
        try:size=int(self.headers.get("Content-Length","0"))
        except:return self.send(400,{"error":"Tamaño de subida inválido."})
        if size<1 or size>128*1024*1024:return self.send(413,{"error":"El archivo debe pesar entre 1 byte y 128 MB en este MVP."})
        try:
            message=BytesParser(policy=email_policy).parsebytes((f"MIME-Version: 1.0\r\nContent-Type: {content_type}\r\n\r\n").encode()+self.rfile.read(size))
            fields={}; video=None
            for part in message.iter_parts():
                name=part.get_param("name",header="content-disposition")
                payload=part.get_payload(decode=True) or b""
                if name=="video":video=(part.get_filename() or "video.mp4",part.get_content_type(),payload)
                elif name:fields[name]=payload.decode("utf-8",errors="replace")
            if not video:return self.send(400,{"error":"Selecciona un archivo de vídeo."})
            token=youtube_access_token(bid)
            result=youtube.upload_video(token,video[2],video[0],video[1],fields.get("title",""),fields.get("description",""),fields.get("privacyStatus","private"))
            video_id=result.get("id")
            return self.send(201,{"id":video_id,"url":f"https://www.youtube.com/watch?v={video_id}" if video_id else "","title":result.get("snippet",{}).get("title",fields.get("title","")),"privacyStatus":result.get("status",{}).get("privacyStatus",fields.get("privacyStatus","private"))})
        except Exception as exc:return self.send(502,{"error":str(exc)})
    def paypal_webhook(self):
        try:
            size=int(self.headers.get("Content-Length","0"))
            if size<1 or size>1024*1024: return self.send(413,{"error":"Webhook demasiado grande."})
            raw=self.rfile.read(size)
            if not paypal.verify_webhook(raw,self.headers): return self.send(400,{"error":"Firma de webhook de PayPal no válida."})
            event=json.loads(raw); event_id=str(event.get("id","")); event_type=str(event.get("event_type",""))
            resource=event.get("resource") or {}
            if not event_id: return self.send(400,{"error":"Evento sin identificador."})
            status_map={"BILLING.SUBSCRIPTION.ACTIVATED":"active","BILLING.SUBSCRIPTION.CANCELLED":"cancelled","BILLING.SUBSCRIPTION.SUSPENDED":"suspended","BILLING.SUBSCRIPTION.EXPIRED":"expired","BILLING.SUBSCRIPTION.PAYMENT.FAILED":"past_due","PAYMENT.SALE.COMPLETED":"active","PAYMENT.SALE.FAILED":"past_due"}
            if event_type=="BILLING.SUBSCRIPTION.UPDATED":
                status_map[event_type]={"ACTIVE":"active","APPROVED":"active","SUSPENDED":"suspended","CANCELLED":"cancelled","EXPIRED":"expired"}.get(str(resource.get("status","")).upper(),"past_due")
            new_status=status_map.get(event_type)
            subscription_id=str(resource.get("billing_agreement_id") or resource.get("id") or "")
            if not new_status or not subscription_id: return self.send(200,{"ok":True,"ignored":True})
            with db() as c:
                if c.execute("SELECT 1 FROM billing_events WHERE provider='paypal' AND event_id=?",(event_id,)).fetchone():
                    return self.send(200,{"ok":True,"duplicate":True})
                row=c.execute("SELECT user_id,plan_key FROM subscriptions WHERE external_subscription_id=?",(subscription_id,)).fetchone()
                if not row:
                    try: uid=int(resource.get("custom_id",""))
                    except (TypeError,ValueError): uid=0
                    plan_id=str(resource.get("plan_id",""))
                    plans=paypal.config()["plans"]
                    plan_key=next((k for k,v in plans.items() if v and v==plan_id),None)
                    if not uid or not plan_key or not c.execute("SELECT 1 FROM users WHERE id=?",(uid,)).fetchone():
                        return self.send(200,{"ok":True,"ignored":True})
                else:
                    uid=row["user_id"]
                    plan_key=row["plan_key"]
                period_end=(resource.get("billing_info") or {}).get("next_billing_time")
                c.execute("INSERT INTO billing_events(provider,event_id,event_type,processed_at) VALUES('paypal',?,?,?)",(event_id,event_type,now()))
                c.execute("INSERT INTO subscriptions(user_id,provider,external_subscription_id,plan_key,status,current_period_end,updated_at) VALUES(?,'paypal',?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET provider='paypal',external_subscription_id=excluded.external_subscription_id,plan_key=excluded.plan_key,status=excluded.status,current_period_end=COALESCE(excluded.current_period_end,subscriptions.current_period_end),updated_at=excluded.updated_at",
                          (uid,subscription_id,plan_key,new_status,period_end,now()))
            return self.send(200,{"ok":True})
        except Exception as exc:
            return self.send(400,{"error":str(exc)})

    def do_POST(self):
        if urlparse(self.path).path=="/api/integrations/paypal/webhook": return self.paypal_webhook()
        path=urlparse(self.path).path
        if path.startswith("/api/brand/") and path.endswith("/youtube/publish"):
            return self.youtube_publish(path)
        try: data=self.body()
        except: return self.send(400,{"error":"JSON inválido"})
        if path=="/api/register":
            email=str(data.get("email","")).strip().lower(); pw=str(data.get("password",""))
            if "@" not in email or len(pw)<10:return self.send(400,{"error":"Usa un email válido y una contraseña de al menos 10 caracteres."})
            salt=secrets.token_hex(16)
            try:
                with db() as c:
                    cur=c.execute("INSERT INTO users(email,salt,password,created_at) VALUES(?,?,?,?)",(email,salt,digest(pw,salt),now())); uid=cur.lastrowid
                    cur=c.execute("INSERT INTO brands(user_id,name,niche,voice,audience,created_at) VALUES(?,?,?,?,?,?)",(uid,"Mi primera marca","","Cercana, experta y clara","",now())); bid=cur.lastrowid
                    c.execute("INSERT INTO workflows(brand_id,name,prompt,cadence,enabled) VALUES(?,?,?,?,?)",(bid,"Plan semanal","Propón 5 ideas priorizadas según mi marca", "weekly",0))
                    token=secrets.token_urlsafe(32); c.execute("INSERT INTO sessions VALUES(?,?,?)",(token,uid,int(time.time())+2592000))
                self.send_response(201); self.send_header("Set-Cookie",f"aion_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=2592000"); self.send_header("Content-Type","application/json"); self.end_headers(); self.wfile.write(b'{"ok":true}')
            except sqlite3.IntegrityError:return self.send(409,{"error":"Ese email ya está registrado."})
            return
        if path=="/api/login":
            email=str(data.get("email","")).strip().lower()
            with db() as c: row=c.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone()
            if not row or not hmac.compare_digest(digest(str(data.get("password","")),row["salt"]),row["password"]):return self.send(401,{"error":"Email o contraseña incorrectos."})
            token=secrets.token_urlsafe(32)
            with db() as c:c.execute("INSERT INTO sessions VALUES(?,?,?)",(token,row["id"],int(time.time())+2592000))
            self.send_response(200); self.send_header("Set-Cookie",f"aion_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=2592000"); self.send_header("Content-Type","application/json"); self.end_headers(); self.wfile.write(b'{"ok":true}'); return
        u=self.auth()
        if not u:return
        if path=="/api/billing/subscription/confirm":
            plan_key=str(data.get("planKey",""))
            subscription_id=str(data.get("subscriptionId","")).strip()
            expected=paypal.config()["plans"].get(plan_key)
            if plan_key not in ("creator","studio") or not expected or not subscription_id:
                return self.send(400,{"error":"Plan o suscripción de PayPal no configurados."})
            try:
                remote=paypal.get_subscription(subscription_id)
                if remote.get("id")!=subscription_id or remote.get("plan_id")!=expected or str(remote.get("custom_id",""))!=str(u):
                    return self.send(403,{"error":"La suscripción de PayPal no corresponde a esta cuenta y plan."})
                if str(remote.get("status","")).upper() not in ("ACTIVE","APPROVED"):
                    return self.send(409,{"error":"PayPal aún no confirma el pago de la suscripción."})
                current=(remote.get("billing_info") or {}).get("next_billing_time")
                with db() as c:
                    old=c.execute("SELECT external_subscription_id,status FROM subscriptions WHERE user_id=?",(u,)).fetchone()
                    if old and old["external_subscription_id"]!=subscription_id and old["status"] in ("active","trialing","past_due"):
                        return self.send(409,{"error":"Ya hay una suscripción activa. Cancélala en PayPal antes de cambiar de plan."})
                    c.execute("INSERT INTO subscriptions(user_id,provider,external_subscription_id,plan_key,status,current_period_end,updated_at) VALUES(?,'paypal',?,?, 'active',?,?) ON CONFLICT(user_id) DO UPDATE SET provider='paypal',external_subscription_id=excluded.external_subscription_id,plan_key=excluded.plan_key,status='active',current_period_end=excluded.current_period_end,updated_at=excluded.updated_at",
                              (u,subscription_id,plan_key,current,now()))
                return self.send(200,{"ok":True})
            except Exception as exc:
                return self.send(502,{"error":str(exc)})
        with db() as c:
            def owned(bid): return c.execute("SELECT id FROM brands WHERE id=? AND user_id=?",(bid,u)).fetchone()
            if path=="/api/logout":
                token=self.headers.get("Cookie","").replace("aion_session=","").split(";",1)[0]; c.execute("DELETE FROM sessions WHERE token=?",(token,)); self.send_response(200); self.send_header("Set-Cookie","aion_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0"); self.end_headers(); return
            if path=="/api/brands":
                name=str(data.get("name","")).strip()
                if not name:return self.send(400,{"error":"El nombre de marca es obligatorio."})
                account=billing.snapshot(c,u)
                if account["brands"]["remaining"]<=0:return self.send(402,{"error":f"Tu plan {account['name']} alcanzó el límite de marcas. Revisa Plan y facturación.","billing":account})
                cur=c.execute("INSERT INTO brands(user_id,name,niche,voice,audience,created_at) VALUES(?,?,?,?,?,?)",(u,name,data.get("niche",""),data.get("voice",""),data.get("audience",""),now())); return self.send(201,{"id":cur.lastrowid})
            if path.startswith("/api/brand/"):
                bits=path.split("/");
                try: bid=int(bits[3])
                except: return self.send(400,{"error":"ID inválido"})
                if not owned(bid):return self.send(404,{"error":"Marca no encontrada"})
                action=bits[4] if len(bits)>4 else ""
                if action=="update":
                    c.execute("UPDATE brands SET name=?,niche=?,voice=?,audience=? WHERE id=?",(data.get("name",""),data.get("niche",""),data.get("voice",""),data.get("audience",""),bid)); return self.send(200,{"ok":True})
                if action=="project":
                    title=str(data.get("title","")).strip()
                    if not title:return self.send(400,{"error":"El título es obligatorio."})
                    cur=c.execute("INSERT INTO projects(brand_id,title,platform,status,idea,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",(bid,title,data.get("platform","YouTube"),data.get("status","idea"),data.get("idea",""),now(),now())); return self.send(201,{"id":cur.lastrowid})
                if action=="asset":
                    cur=c.execute("INSERT INTO assets(brand_id,name,kind,url,notes,created_at) VALUES(?,?,?,?,?,?)",(bid,data.get("name","Activo"),data.get("kind","note"),data.get("url",""),data.get("notes",""),now())); return self.send(201,{"id":cur.lastrowid})
                if action=="metric":
                    cur=c.execute("INSERT INTO metrics(brand_id,platform,label,views,followers,revenue,measured_at) VALUES(?,?,?,?,?,?,?)",(bid,data.get("platform","YouTube"),data.get("label","Registro manual"),int(data.get("views",0)),int(data.get("followers",0)),float(data.get("revenue",0)),now())); return self.send(201,{"id":cur.lastrowid})
                if action=="workflow":
                    cur=c.execute("INSERT INTO workflows(brand_id,name,prompt,cadence,enabled) VALUES(?,?,?,?,?)",(bid,data.get("name","Flujo nuevo"),data.get("prompt",""),data.get("cadence","manual"),int(data.get("enabled",0)))); return self.send(201,{"id":cur.lastrowid})
                if action=="generate":
                    kind=data.get("kind"); detail=data.get("detail","")
                    b=c.execute("SELECT * FROM brands WHERE id=?",(bid,)).fetchone()
                    project=c.execute("SELECT * FROM projects WHERE id=? AND brand_id=?",(data.get("projectId"),bid)).fetchone() if data.get("projectId") else None
                    if kind=="ideas": prompt=f"Investiga y propone 8 ideas de contenido para marca {b['name']}, nicho {b['niche']}, audiencia {b['audience']}. Solicitud: {detail}. Para cada una, indica hipótesis de oportunidad (no afirmes métricas actuales sin fuente), gancho, formato y por qué encaja. En tabla Markdown."
                    elif kind=="script": prompt=f"Crea un guion detallado para {project['title'] if project else detail}. Marca {b['name']}, tono {b['voice']}, audiencia {b['audience']}. Incluye gancho, segmentos con narración y visuales, CTA y duración estimada."
                    elif kind=="storyboard": prompt=f"Genera storyboard por escenas para {project['title'] if project else detail}; columnas: tiempo, narración, imagen/acción, texto en pantalla, audio. Marca: {b['name']}."
                    elif kind=="seo": prompt=f"Optimiza el contenido {project['title'] if project else detail} para {project['platform'] if project else 'YouTube'}. Entrega título, 3 variantes, descripción, palabras clave, hashtags y texto de miniatura. No inventes datos de tendencias."
                    elif kind=="workflow": prompt=f"Ejecuta este flujo para la marca {b['name']} (nicho {b['niche']}, tono {b['voice']}): {detail}. Devuelve pasos accionables con salida lista para revisar."
                    else:return self.send(400,{"error":"Tipo de generación desconocido."})
                    account=billing.snapshot(c,u)
                    if account["usage"]["remaining"]<=0:return self.send(402,{"error":f"Has alcanzado las {account['usage']['monthlyAiLimit']} generaciones IA mensuales de tu plan {account['name']}. Consulta Plan y facturación para ampliar el límite.","billing":account})
                    cur=c.execute("INSERT INTO jobs(brand_id,kind,status,created_at) VALUES(?,?,?,?)",(bid,kind,"running",now())); jid=cur.lastrowid
                    reserved=billing.reserve_ai_generation(c,u,account["key"])
                    if not reserved:
                        account=billing.snapshot(c,u)
                        c.execute("UPDATE jobs SET status='failed',result=?,finished_at=? WHERE id=?",("Cuota mensual agotada",now(),jid))
                        return self.send(402,{"error":"Límite mensual de IA alcanzado.","billing":account})
                    try:
                        result=ai(prompt); c.execute("UPDATE jobs SET status='completed',result=?,finished_at=? WHERE id=?",(result,now(),jid))
                        if project and kind in ("script","storyboard","seo"):
                            field={"script":"script","storyboard":"storyboard","seo":"seo"}[kind]; c.execute(f"UPDATE projects SET {field}=?,updated_at=? WHERE id=?",(result,now(),project["id"]))
                        return self.send(200,{"id":jid,"result":result})
                    except Exception as e:
                        billing.release_ai_generation(c,u)
                        c.execute("UPDATE jobs SET status='failed',result=?,finished_at=? WHERE id=?",(str(e),now(),jid)); return self.send(503,{"error":str(e),"jobId":jid})
                return self.send(404,{"error":"Acción desconocida"})
        return self.send(404,{"error":"Ruta no encontrada"})

if __name__=="__main__":
    print(f"AION STUDIO disponible en http://localhost:{PORT}")
    ThreadingHTTPServer(("0.0.0.0",PORT),Handler).serve_forever()
