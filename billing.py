"""Provider-neutral plan definitions and metered usage."""
from datetime import datetime, timezone
PLANS={"free":{"name":"Free","monthly_ai_runs":5,"brand_limit":1},"creator":{"name":"Creator","monthly_ai_runs":100,"brand_limit":3},"studio":{"name":"Studio","monthly_ai_runs":500,"brand_limit":10}}
ACTIVE_STATUSES={"active","trialing"}
def period_key(): return datetime.now(timezone.utc).strftime("%Y-%m")
def snapshot(conn,user_id):
 sub=conn.execute("SELECT plan_key,status,provider,current_period_end FROM subscriptions WHERE user_id=?",(user_id,)).fetchone()
 key=sub["plan_key"] if sub and sub["status"] in ACTIVE_STATUSES else "free"
 plan=PLANS.get(key,PLANS["free"]); period=period_key()
 row=conn.execute("SELECT ai_generations FROM ai_usage WHERE user_id=? AND period=?",(user_id,period)).fetchone(); used=int(row[0]) if row else 0
 brands=int(conn.execute("SELECT COUNT(*) FROM brands WHERE user_id=?",(user_id,)).fetchone()[0])
 return {"key":key,"name":plan["name"],"status":sub["status"] if sub else "free","provider":sub["provider"] if sub else None,"currentPeriodEnd":sub["current_period_end"] if sub else None,"usage":{"period":period,"aiGenerations":used,"monthlyAiLimit":plan["monthly_ai_runs"],"remaining":max(0,plan["monthly_ai_runs"]-used)},"brands":{"used":brands,"limit":plan["brand_limit"],"remaining":max(0,plan["brand_limit"]-brands)}}
def reserve_ai_generation(conn,user_id,plan_key):
 limit=PLANS.get(plan_key,PLANS["free"])["monthly_ai_runs"]; period=period_key()
 conn.execute("INSERT OR IGNORE INTO ai_usage(user_id,period,ai_generations) VALUES(?,?,0)",(user_id,period))
 cur=conn.execute("UPDATE ai_usage SET ai_generations=ai_generations+1 WHERE user_id=? AND period=? AND ai_generations<?",(user_id,period,limit)); return cur.rowcount==1
def release_ai_generation(conn,user_id): conn.execute("UPDATE ai_usage SET ai_generations=MAX(0,ai_generations-1) WHERE user_id=? AND period=?",(user_id,period_key()))
def public_plans(): return [{"key":k,"name":v["name"],"monthlyAiLimit":v["monthly_ai_runs"],"brandLimit":v["brand_limit"]} for k,v in PLANS.items()]
