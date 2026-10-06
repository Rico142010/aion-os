* {
  box-sizing: border-box;
}

:root {
  --bg: #07111f;
  --panel: #0d1b2a;
  --panel-2: #12263d;
  --accent: #67e8f9;
  --accent-2: #8b5cf6;
  --text: #e2e8f0;
  --muted: #94a3b8;
  --success: #22c55e;
  --warning: #f59e0b;
}

body {
  margin: 0;
  font-family: Arial, Helvetica, sans-serif;
  background: linear-gradient(135deg, var(--bg), #0f172a);
  color: var(--text);
}

.shell {
  max-width: 1100px;
  margin: 0 auto;
  padding: 40px 20px 80px;
}

.hero {
  padding: 32px 0 24px;
}

.badge {
  display: inline-block;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(103, 232, 249, 0.12);
  border: 1px solid rgba(103, 232, 249, 0.25);
  color: var(--accent);
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-size: 12px;
}

.hero h1 {
  margin: 18px 0 12px;
  font-size: clamp(2.2rem, 5vw, 4rem);
  line-height: 1.1;
}

.hero p {
  margin: 0;
  max-width: 700px;
  color: var(--muted);
  font-size: 1.08rem;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 20px;
}

.card {
  background: rgba(17, 24, 39, 0.8);
  border: 1px solid rgba(148, 163, 184, 0.15);
  border-radius: 18px;
  padding: 22px;
  box-shadow: 0 20px 50px rgba(15, 23, 42, 0.35);
}

.card h2 {
  margin-top: 0;
  font-size: 1.2rem;
}

.card ul {
  margin: 16px 0 0;
  padding-left: 18px;
  color: var(--muted);
  line-height: 1.9;
}

.card p {
  color: var(--muted);
  line-height: 1.7;
  margin: 0;
}

.wide {
  grid-column: 1 / -1;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 999px;
  font-weight: 700;
  margin-bottom: 12px;
}

.loading {
  background: rgba(245, 158, 11, 0.12);
  color: var(--warning);
  border: 1px solid rgba(245, 158, 11, 0.25);
}

.success {
  background: rgba(34, 197, 94, 0.12);
  color: var(--success);
  border: 1px solid rgba(34, 197, 94, 0.25);
}
