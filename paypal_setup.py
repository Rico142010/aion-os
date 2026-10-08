"""Create AION monthly subscription plans in PayPal Sandbox from local .env values."""
import os
import re
import sys
import uuid
from decimal import Decimal, InvalidOperation
from pathlib import Path

import paypal

ROOT = Path(__file__).parent
ENV_FILE = ROOT / ".env"


def load_env():
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def set_env(key, value):
    lines = ENV_FILE.read_text(encoding="utf-8-sig").splitlines() if ENV_FILE.exists() else []
    updated = False
    for i, line in enumerate(lines):
        if line.startswith(key + "="):
            lines[i] = key + "=" + value
            updated = True
            break
    if not updated:
        lines.append(key + "=" + value)
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_inputs():
    if os.getenv("PAYPAL_MODE", "sandbox").strip().lower() != "sandbox":
        raise ValueError("Plan setup only runs in Sandbox. Switch PAYPAL_MODE=sandbox first.")
    if not os.getenv("PAYPAL_CLIENT_ID", "").strip() or not os.getenv("PAYPAL_CLIENT_SECRET", "").strip():
        raise ValueError("Set the Sandbox PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET in .env.")
    currency = os.getenv("PAYPAL_CURRENCY", "USD").strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", currency):
        raise ValueError("PAYPAL_CURRENCY must be a 3-letter ISO currency code.")
    prices = {}
    for key in ("creator", "studio"):
        raw = os.getenv("PAYPAL_PRICE_" + key.upper(), "").strip()
        try:
            amount = Decimal(raw)
        except InvalidOperation:
            raise ValueError("Set positive monthly amounts in PAYPAL_PRICE_CREATOR and PAYPAL_PRICE_STUDIO.") from None
        if not amount.is_finite() or amount <= 0:
            raise ValueError("Set positive monthly amounts in PAYPAL_PRICE_CREATOR and PAYPAL_PRICE_STUDIO.")
        prices[key] = format(amount, "f")
    return currency, prices


def create_plan(token, product_id, key, price, currency):
    plan_name = "AION STUDIO " + key.title()
    body = {
        "product_id": product_id,
        "name": plan_name + " Monthly",
        "description": "Monthly " + key.title() + " subscription for AION STUDIO",
        "billing_cycles": [{
            "frequency": {"interval_unit": "MONTH", "interval_count": 1},
            "tenure_type": "REGULAR",
            "sequence": 1,
            "total_cycles": 0,
            "pricing_scheme": {"fixed_price": {"value": price, "currency_code": currency}},
        }],
        "payment_preferences": {"auto_bill_outstanding": True, "payment_failure_threshold": 3},
    }
    result = paypal._request("POST", "/v1/billing/plans", token, body,
                             {"PayPal-Request-Id": str(uuid.uuid4())})
    plan_id = result.get("id")
    if not plan_id:
        raise ValueError("PayPal did not return a plan ID for " + key + ".")
    if str(result.get("status", "")).upper() != "ACTIVE":
        paypal._request("POST", "/v1/billing/plans/" + plan_id + "/activate", token)
    env_key = "PAYPAL_PLAN_" + key.upper()
    set_env(env_key, plan_id)
    os.environ[env_key] = plan_id
    print(env_key + " configured (" + plan_id + ")")


def main():
    load_env()
    currency, prices = validate_inputs()
    token = paypal.access_token()
    product_id = os.getenv("PAYPAL_PRODUCT_ID", "").strip()
    if not product_id:
        product = paypal._request("POST", "/v1/catalogs/products", token, {
            "name": "AION STUDIO",
            "description": "AI-powered content creation and management platform",
            "type": "SERVICE",
        }, {"PayPal-Request-Id": str(uuid.uuid4())})
        product_id = product.get("id", "")
        if not product_id:
            raise ValueError("PayPal did not return a product ID.")
        set_env("PAYPAL_PRODUCT_ID", product_id)
        os.environ["PAYPAL_PRODUCT_ID"] = product_id
        print("AION product created (" + product_id + ")")
    for key in ("creator", "studio"):
        if os.getenv("PAYPAL_PLAN_" + key.upper(), "").strip():
            print("PAYPAL_PLAN_" + key.upper() + " already set; skipping.")
            continue
        create_plan(token, product_id, key, prices[key], currency)
    print("Sandbox plans are ready. Configure and verify the public HTTPS webhook before testing subscription lifecycle events.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("PayPal Sandbox setup failed: " + str(exc), file=sys.stderr)
        raise SystemExit(1)