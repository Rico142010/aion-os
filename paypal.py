"""PayPal Subscriptions REST API adapter; secrets remain server-side."""
import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request

def config():
    mode = os.getenv("PAYPAL_MODE", "sandbox").strip().lower()
    if mode not in ("sandbox", "live"):
        mode = "sandbox"
    return {"mode": mode,
            "base": "https://api-m.sandbox.paypal.com" if mode == "sandbox" else "https://api-m.paypal.com",
            "client_id": os.getenv("PAYPAL_CLIENT_ID", "").strip(),
            "client_secret": os.getenv("PAYPAL_CLIENT_SECRET", "").strip(),
            "webhook_id": os.getenv("PAYPAL_WEBHOOK_ID", "").strip(),
            "plans": {"creator": os.getenv("PAYPAL_PLAN_CREATOR", "").strip(),
                      "studio": os.getenv("PAYPAL_PLAN_STUDIO", "").strip()}}

def public_config():
    c = config()
    return {"enabled": bool(c["client_id"] and c["client_secret"] and c["webhook_id"] and c["plans"]["creator"] and c["plans"]["studio"]),
            "clientId": c["client_id"], "mode": c["mode"], "planIds": c["plans"]}

def _request(method, path, token=None, payload=None, extra_headers=None):
    c = config()
    body = json.dumps(payload).encode() if payload is not None else None
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(c["base"] + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            raw = response.read()
        return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:1000]
        raise ValueError(f"PayPal HTTP {exc.code}: {detail}") from None
    except urllib.error.URLError as exc:
        raise ValueError(f"PayPal connection failed: {exc.reason}") from None

def access_token():
    c = config()
    if not c["client_id"] or not c["client_secret"]:
        raise ValueError("Set PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET in .env.")
    auth = (c["client_id"] + ":" + c["client_secret"]).encode()
    req = urllib.request.Request(c["base"] + "/v1/oauth2/token", data=b"grant_type=client_credentials",
        headers={"Authorization": "Basic " + base64.b64encode(auth).decode(),
                 "Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            return json.loads(response.read())["access_token"]
    except urllib.error.HTTPError as exc:
        raise ValueError(f"PayPal authentication failed ({exc.code}); check credentials and {c['mode']} mode.") from None
    except urllib.error.URLError as exc:
        raise ValueError(f"PayPal connection failed: {exc.reason}") from None

def get_subscription(subscription_id):
    path = "/v1/billing/subscriptions/" + urllib.parse.quote(subscription_id, safe="")
    return _request("GET", path, access_token())

def verify_webhook(raw_body, headers):
    c = config()
    if not c["webhook_id"]:
        raise ValueError("PAYPAL_WEBHOOK_ID is not configured.")
    payload = {"auth_algo": headers.get("paypal-auth-algo", ""),
        "cert_url": headers.get("paypal-cert-url", ""),
        "transmission_id": headers.get("paypal-transmission-id", ""),
        "transmission_sig": headers.get("paypal-transmission-sig", ""),
        "transmission_time": headers.get("paypal-transmission-time", ""),
        "webhook_id": c["webhook_id"], "webhook_event": json.loads(raw_body)}
    required = ("auth_algo", "cert_url", "transmission_id", "transmission_sig", "transmission_time")
    if not all(payload[k] for k in required):
        raise ValueError("Missing PayPal webhook verification headers.")
    result = _request("POST", "/v1/notifications/verify-webhook-signature",
                      access_token(), payload)
    return result.get("verification_status") == "SUCCESS"

