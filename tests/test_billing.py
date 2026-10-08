import sqlite3
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import billing

class BillingPlanTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(":memory:")
        self.db.row_factory=sqlite3.Row
        self.db.executescript("CREATE TABLE subscriptions(user_id INTEGER PRIMARY KEY,provider TEXT,external_subscription_id TEXT,plan_key TEXT,status TEXT,current_period_end TEXT,updated_at TEXT); CREATE TABLE ai_usage(user_id INTEGER,period TEXT,ai_generations INTEGER,PRIMARY KEY(user_id,period)); CREATE TABLE brands(id INTEGER PRIMARY KEY,user_id INTEGER);")
        self.db.execute("INSERT INTO brands(user_id) VALUES(1)")
    def tearDown(self): self.db.close()
    def test_free_account_has_monthly_limits(self):
        state=billing.snapshot(self.db,1)
        self.assertEqual(state["key"],"free")
        self.assertEqual(state["usage"]["remaining"],5)
        self.assertEqual(state["brands"]["limit"],1)
    def test_active_plan_quota_and_reservation(self):
        self.db.execute("INSERT INTO subscriptions(user_id,provider,plan_key,status) VALUES(1,'paypal','creator','active')")
        for _ in range(100): self.assertTrue(billing.reserve_ai_generation(self.db,1,"creator"))
        self.assertFalse(billing.reserve_ai_generation(self.db,1,"creator"))
        self.assertEqual(billing.snapshot(self.db,1)["usage"]["remaining"],0)
        billing.release_ai_generation(self.db,1)
        self.assertEqual(billing.snapshot(self.db,1)["usage"]["remaining"],1)

if __name__=="__main__":unittest.main()
