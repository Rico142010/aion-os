"""Small YouTube OAuth/Data API adapter using Google's documented REST endpoints."""
import json
import mimetypes
import os
import base64
import secrets
import urllib.error
import urllib.parse
import urllib.request
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

AUTHORIZE = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN = "https://oauth2.googleapis.com/token"
DATA_API = "https://www.googleapis.com/youtube/v3"
ANALYTICS_API = "https://youtubeanalytics.googleapis.com/v2/reports"
SCOPES = (
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
)

def config():
    return (os.getenv("YOUTUBE_CLIENT_ID", "").strip(),
            os.getenv("YOUTUBE_CLIENT_SECRET", "").strip(),
            os.getenv("YOUTUBE_REDIRECT_URI", "http://localhost:8000/api/integrations/youtube/callback").strip())

def configured():
    client, secret, _ = config()
    try:
        _token_key()
    except ValueError:
        return False
    return bool(client and secret)

def authorization_url(state):
    client, _, redirect = config()
    if not client:
        raise ValueError("Configura YOUTUBE_CLIENT_ID y YOUTUBE_CLIENT_SECRET en .env")
    params = {"client_id": client, "redirect_uri": redirect, "response_type": "code",
              "scope": " ".join(SCOPES), "access_type": "offline", "include_granted_scopes": "true",
              "prompt": "consent", "state": state}
    return AUTHORIZE + "?" + urllib.parse.urlencode(params)

def _post_form(url, fields):
    payload = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:500]
        raise ValueError(f"Google OAuth respondió {exc.code}: {detail}") from None
    except urllib.error.URLError as exc:
        raise ValueError(f"No se pudo conectar con Google OAuth: {exc.reason}") from None

def exchange_code(code):
    client, secret, redirect = config()
    return _post_form(TOKEN, {"code": code, "client_id": client, "client_secret": secret,
                              "redirect_uri": redirect, "grant_type": "authorization_code"})

def refresh(refresh_token):
    client, secret, _ = config()
    return _post_form(TOKEN, {"refresh_token": refresh_token, "client_id": client,
                              "client_secret": secret, "grant_type": "refresh_token"})

def api_get(url, access_token):
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + access_token,
                                               "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:500]
        raise ValueError(f"YouTube API respondió {exc.code}: {detail}") from None
    except urllib.error.URLError as exc:
        raise ValueError(f"No se pudo conectar con YouTube: {exc.reason}") from None

def channel(access_token):
    url = DATA_API + "/channels?" + urllib.parse.urlencode({"part": "snippet,statistics", "mine": "true"})
    response = api_get(url, access_token)
    items = response.get("items", [])
    if not items:
        raise ValueError("La cuenta autorizada no tiene un canal de YouTube accesible.")
    item = items[0]
    return {"id": item["id"], "title": item["snippet"].get("title", "YouTube"),
            "subscribers": int(item.get("statistics", {}).get("subscriberCount", 0)),
            "views": int(item.get("statistics", {}).get("viewCount", 0)),
            "videoCount": int(item.get("statistics", {}).get("videoCount", 0))}

def analytics(access_token, start_date, end_date):
    params = {"ids": "channel==MINE", "startDate": start_date, "endDate": end_date,
              "metrics": "views,likes,comments,subscribersGained,estimatedMinutesWatched",
              "dimensions": "day", "sort": "day"}
    return api_get(ANALYTICS_API + "?" + urllib.parse.urlencode(params), access_token)

def upload_video(access_token, video_bytes, filename, mime_type, title, description, privacy):
    if not mime_type.startswith("video/"):
        raise ValueError("Selecciona un archivo de vídeo válido.")
    if privacy not in ("private", "unlisted", "public"):
        raise ValueError("La visibilidad debe ser private, unlisted o public.")
    if len(title.strip()) < 1 or len(title) > 100:
        raise ValueError("El título debe tener entre 1 y 100 caracteres.")
    if len(description) > 5000:
        raise ValueError("La descripción no puede superar 5000 caracteres.")
    metadata = {"snippet": {"title": title.strip(), "description": description},
                "status": {"privacyStatus": privacy}}
    start = DATA_API.replace("www.googleapis.com/youtube/v3", "www.googleapis.com/upload/youtube/v3")
    url = start + "/videos?uploadType=resumable&part=snippet,status"
    init = urllib.request.Request(url, data=json.dumps(metadata).encode(), method="POST", headers={
        "Authorization": "Bearer " + access_token, "Content-Type": "application/json; charset=UTF-8",
        "X-Upload-Content-Length": str(len(video_bytes)),
        "X-Upload-Content-Type": mime_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"})
    try:
        with urllib.request.urlopen(init, timeout=30) as response:
            upload_url = response.headers.get("Location")
        if not upload_url: raise ValueError("Google no devolvió una sesión de subida resumible.")
        req = urllib.request.Request(upload_url, data=video_bytes, method="PUT", headers={
            "Authorization": "Bearer " + access_token, "Content-Type": mime_type,
            "Content-Length": str(len(video_bytes)), "Content-Range": f"bytes 0-{len(video_bytes)-1}/{len(video_bytes)}"})
        with urllib.request.urlopen(req, timeout=600) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:500]
        raise ValueError(f"YouTube rechazó la subida ({exc.code}): {detail}") from None
    except urllib.error.URLError as exc:
        raise ValueError(f"No se pudo conectar con YouTube para subir el vídeo: {exc.reason}") from None

def _token_key():
    encoded=os.getenv("YOUTUBE_TOKEN_ENCRYPTION_KEY","").strip()
    if not encoded: raise ValueError("Falta YOUTUBE_TOKEN_ENCRYPTION_KEY en .env para cifrar el refresh token.")
    try:key=base64.urlsafe_b64decode(encoded.encode())
    except Exception:raise ValueError("YOUTUBE_TOKEN_ENCRYPTION_KEY debe ser una clave Base64 URL-safe de 32 bytes.") from None
    if len(key)!=32:raise ValueError("YOUTUBE_TOKEN_ENCRYPTION_KEY debe decodificar exactamente a 32 bytes.")
    return key

def protect(data):
    """Encrypt stored OAuth credentials using authenticated AES-256-GCM."""
    nonce=secrets.token_bytes(12)
    encrypted=AESGCM(_token_key()).encrypt(nonce,json.dumps(data).encode(),b"AION YouTube OAuth v1")
    return b"AY1"+nonce+encrypted

def unprotect(blob):
    if not blob.startswith(b"AY1") or len(blob)<32:raise ValueError("El token OAuth cifrado tiene un formato inválido.")
    return json.loads(AESGCM(_token_key()).decrypt(blob[3:15],blob[15:],b"AION YouTube OAuth v1"))
