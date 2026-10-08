import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import youtube

class YouTubeOAuthTests(unittest.TestCase):
    def test_authorization_url_uses_local_callback_and_limited_scopes(self):
        with patch.dict(os.environ,{
            "YOUTUBE_CLIENT_ID":"example-client.apps.googleusercontent.com",
            "YOUTUBE_CLIENT_SECRET":"test-secret",
            "YOUTUBE_REDIRECT_URI":"http://localhost:8000/api/integrations/youtube/callback",
        }):
            parsed=parse_qs(urlsplit(youtube.authorization_url("state-123")).query)
        self.assertEqual(parsed["state"],["state-123"])
        self.assertEqual(parsed["redirect_uri"],["http://localhost:8000/api/integrations/youtube/callback"])
        self.assertEqual(parsed["access_type"],["offline"])
        self.assertIn("https://www.googleapis.com/auth/youtube.upload",parsed["scope"][0])
        self.assertIn("https://www.googleapis.com/auth/yt-analytics.readonly",parsed["scope"][0])

    def test_encrypted_token_roundtrip(self):
        key=__import__("base64").urlsafe_b64encode(b"k"*32).decode()
        data={"access_token":"sample-access","refresh_token":"sample-refresh","expires_at":123}
        with patch.dict(os.environ,{"YOUTUBE_TOKEN_ENCRYPTION_KEY":key}):
            protected=youtube.protect(data)
            restored=youtube.unprotect(protected)
        self.assertNotIn(b"sample-refresh",protected)
        self.assertEqual(restored,data)

if __name__=="__main__":unittest.main()
