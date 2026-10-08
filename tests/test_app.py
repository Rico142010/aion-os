import http.cookies
import importlib.util
import json
import os
import tempfile
import threading
import unittest
import urllib.request
from unittest.mock import patch

TEMP = tempfile.TemporaryDirectory()
os.environ["DATABASE_PATH"] = os.path.join(TEMP.name, "test.db")
spec = importlib.util.spec_from_file_location("aion_app", os.path.join(os.path.dirname(__file__), "..", "app.py"))
app = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = app
spec.loader.exec_module(app)

class FlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = app.ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def call(self, path, method="GET", body=None, cookie=None):
        headers={"Content-Type":"application/json"}
        if cookie: headers["Cookie"]=cookie
        req=urllib.request.Request(self.base+path, data=json.dumps(body).encode() if body is not None else None, headers=headers, method=method)
        with urllib.request.urlopen(req) as res: return res.status, res.headers, json.loads(res.read() or b"{}")

    def test_ai_uses_configurable_openai_compatible_provider(self):
        response = {"choices": [{"message": {"content": "Guion listo"}}]}
        with patch.object(app, "AI_KEY", "test-key"), \
             patch.object(app, "AI_PROVIDER", "custom-provider"), \
             patch.object(app, "AI_BASE_URL", "https://ai.example.test/v1"), \
             patch.object(app, "AI_MODEL", "test-model"), \
             patch.object(app.urllib.request, "urlopen") as urlopen:
            urlopen.return_value.__enter__.return_value.read.return_value = json.dumps(response).encode()
            self.assertEqual(app.ai("Crea una idea"), "Guion listo")
            request = urlopen.call_args.args[0]
            self.assertEqual(request.full_url, "https://ai.example.test/v1/chat/completions")
            self.assertEqual(request.get_header("Authorization"), "Bearer test-key")
            self.assertEqual(json.loads(request.data)["model"], "test-model")

    def test_ai_rejects_non_https_external_provider(self):
        with patch.object(app, "AI_KEY", "test-key"), \
             patch.object(app, "AI_BASE_URL", "http://ai.example.test/v1"):
            with self.assertRaisesRegex(ValueError, "debe usar HTTPS"):
                app.ai("Crea una idea")

    def test_health_and_registration_content_flow(self):
        status, _, health=self.call("/api/health")
        self.assertEqual(status,200); self.assertTrue(health["ok"])
        _, headers, _=self.call("/api/register","POST",{"email":"creator@example.test","password":"verylongpassword"})
        cookie=headers.get("Set-Cookie").split(";",1)[0]
        _, _, brands=self.call("/api/brands",cookie=cookie)
        brand=brands[0]
        self.assertEqual(brand["name"],"Mi primera marca")
        _, _, project=self.call(f"/api/brand/{brand['id']}/project","POST",{"title":"Mi primer vídeo","platform":"YouTube","idea":"Una guía"},cookie)
        self.assertGreater(project["id"],0)
        with app.db() as conn: count=conn.execute("SELECT count(*) FROM projects").fetchone()[0]
        self.assertEqual(count,1)

    def test_duplicate_email_and_password_policy(self):
        with self.assertRaises(Exception): self.call("/api/register","POST",{"email":"bad@example.test","password":"short"})
        self.call("/api/register","POST",{"email":"another@example.test","password":"correcthorsebattery"})
        with self.assertRaises(Exception): self.call("/api/register","POST",{"email":"another@example.test","password":"correcthorsebattery"})

if __name__=="__main__": unittest.main()
