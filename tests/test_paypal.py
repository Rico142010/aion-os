import os
import unittest
from unittest.mock import patch

import paypal
import paypal_setup


class PayPalConfigTests(unittest.TestCase):
    def test_checkout_stays_disabled_until_all_server_settings_exist(self):
        settings = {
            "PAYPAL_MODE": "sandbox",
            "PAYPAL_CLIENT_ID": "client",
            "PAYPAL_CLIENT_SECRET": "secret",
            "PAYPAL_PLAN_CREATOR": "P-CREATOR",
            "PAYPAL_PLAN_STUDIO": "P-STUDIO",
            "PAYPAL_WEBHOOK_ID": "WH-1",
        }
        with patch.dict(os.environ, settings, clear=True):
            public = paypal.public_config()
            self.assertTrue(public["enabled"])
            self.assertEqual(public["mode"], "sandbox")
            self.assertEqual(public["planIds"]["creator"], "P-CREATOR")
            self.assertNotIn("client_secret", public)
        with patch.dict(os.environ, {"PAYPAL_CLIENT_ID": "client"}, clear=True):
            self.assertFalse(paypal.public_config()["enabled"])

    def test_sandbox_plan_setup_validates_prices_and_refuses_live_mode(self):
        settings = {"PAYPAL_MODE": "sandbox", "PAYPAL_CLIENT_ID": "client",
                    "PAYPAL_CLIENT_SECRET": "secret", "PAYPAL_CURRENCY": "USD",
                    "PAYPAL_PRICE_CREATOR": "9.50", "PAYPAL_PRICE_STUDIO": "24"}
        with patch.dict(os.environ, settings, clear=True):
            currency, prices = paypal_setup.validate_inputs()
            self.assertEqual(currency, "USD")
            self.assertEqual(prices, {"creator": "9.50", "studio": "24"})
        with patch.dict(os.environ, {**settings, "PAYPAL_MODE": "live"}, clear=True):
            with self.assertRaisesRegex(ValueError, "only runs in Sandbox"):
                paypal_setup.validate_inputs()
    def test_mode_is_restricted_to_sandbox_or_live(self):
        with patch.dict(os.environ, {"PAYPAL_MODE": "other"}, clear=True):
            self.assertEqual(paypal.config()["mode"], "sandbox")
            self.assertIn("sandbox", paypal.config()["base"])


if __name__ == "__main__":
    unittest.main()