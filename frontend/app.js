* {
  box-sizing: border-box;
}

:root {
  --bg: #06121c;
  --bg-soft: #0e1d2d;
  --panel: rgba(15, 22, 31, 0.9);
  --panel-alt: #112336;
  --line: rgba(148, 163, 184, 0.18);
  --text: #e5eefb;
  --muted: #9db0c5;
  --primary: #67e8f9;
  --primary-strong: #38bdf8;
  --success: #4ade80;
  --warning: #fbbf24;
  --danger: #f87171;
}

body {
  margin: 0;
  min-height: 100vh;
  font-family: Inter, Arial, sans-serif;
  background: linear-gradient(135deg, #06121c 0%, #0c1725 30%, #0e1d2d 100%);
  color: var(--text);
}

button,
input,
textarea,
select {
  font: inherit;
}

.hidden {
  display: none !important;
}

.auth-shell,
.app-shell {
  min-height: 100vh;
}

.auth-shell {
  display: grid;
  place-items: center;
  padding: 32px;
}

.auth-card {
  width: min(420px, 100%);
  background: rgba(10, 18, 30, 0.9);
  border: 1px solid var(--line);
  border-radius: 20px;
  padding: 32px;
  box-shadow: 0 28px 60px rgba(0, 0, 0, 0.35);
}

.auth-header {
  text-align: center;
  margin-bottom: 24px;
}

.brand-logo {
  width: 60px;
  height: 60px;
  margin: 0 auto 12px;
  display: grid;
  place-items: center;
  border-radius: 18px;
  font-weight: 800;
  font-size: 1.8rem;
  background: linear-gradient(135deg, var(--primary), var(--primary-strong));
  color: #04121e;
}

.brand-logo.large {
  width: 72px;
  height: 72px;
  font-size: 2.2rem;
}

.auth-header h2,
.topbar h1 {
  margin: 0;
}

.auth-header p {
  margin: 8px 0 0;
  color: var(--muted);
}

.login-form,
.crud-form {
  display: grid;
  gap: 12px;
}

.login-form label {
  display: grid;
  gap: 8px;
  color: var(--muted);
  font-size: 0.94rem;
}

.login-form input,
.crud-form input,
.crud-form textarea,
.crud-form select {
  background: rgba(17, 29, 42, 0.8);
  border: 1px solid var(--line);
  border-radius: 12px;
  color: var(--text);
  padding: 10px 12px;
  outline: none;
}

.login-form input:focus,
.crud-form input:focus,
.crud-form textarea:focus,
.crud-form select:focus {
  border-color: rgba(103, 232, 249, 0.8);
  box-shadow: 0 0 0 3px rgba(103, 232, 249, 0.15);
}

.primary-button,
.ghost-button {
  border: none;
  border-radius: 12px;
  padding: 12px 16px;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.primary-button {
  background: linear-gradient(135deg, var(--primary), var(--primary-strong));
  color: #02141d;
  font-weight: 700;
}

.primary-button.compact {
  padding: 9px 12px;
}

.ghost-button {
  background: rgba(148, 163, 184, 0.08);
  color: var(--text);
  border: 1px solid var(--line);
}

.primary-button:hover,
.ghost-button:hover {
  transform: translateY(-1px);
}

.login-message {
  margin-top: 16px;
  min-height: 22px;
  font-size: 0.92rem;
}

.login-message.success { color: var(--success); }
.login-message.error { color: var(--danger); }
.login-message.warning { color: var(--warning); }
.login-message.info { color: var(--primary); }

.app-shell {
  display: grid;
  grid-template-columns: 260px 1fr;
}

.sidebar {
  background: rgba(7, 16, 25, 0.9);
  border-right: 1px solid var(--line);
  padding: 24px 18px;
}

.brand-block {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 28px;
}

.brand-name {
  font-weight: 700;
}

.brand-subtitle {
  color: var(--muted);
  font-size: 0.84rem;
}

.nav {
  display: grid;
  gap: 10px;
}

.nav-item {
  background: transparent;
  border: 1px solid transparent;
  border-radius: 12px;
  color: var(--text);
  padding: 12px 14px;
  text-align: left;
  cursor: pointer;
}

.nav-item.active {
  background: rgba(103, 232, 249, 0.08);
  border-color: rgba(103, 232, 249, 0.2);
  color: var(--primary);
}

.main-panel {
  padding: 28px;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding-bottom: 24px;
}

.eyebrow {
  margin: 0 0 8px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--primary);
  font-size: 0.72rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: rgba(12, 26, 38, 0.8);
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 20px;
}

.stat-card span {
  display: block;
  color: var(--muted);
  margin-bottom: 8px;
}

.stat-card strong {
  font-size: clamp(1.6rem, 3vw, 2.2rem);
}

.stat-card.accent {
  background: linear-gradient(135deg, rgba(103, 232, 249, 0.15), rgba(56, 189, 248, 0.06));
  border-color: rgba(103, 232, 249, 0.2);
}

.panel-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.panel {
  background: rgba(12, 26, 38, 0.8);
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 20px;
}

.panel-header h2 {
  margin: 0 0 12px;
  font-size: 1.2rem;
}

.list {
  list-style: none;
  margin: 12px 0 0;
  padding: 0;
  display: grid;
  gap: 12px;
}

.list li {
  background: rgba(15, 23, 32, 0.9);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 12px 14px;
  display: grid;
  gap: 6px;
}

.list strong {
  font-size: 0.98rem;
}

.list small {
  color: var(--primary);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.list span {
  color: var(--muted);
  line-height: 1.5;
}

@media (max-width: 800px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    border-right: none;
    border-bottom: 1px solid var(--line);
  }

  .topbar {
    flex-direction: column;
    align-items: flex-start;
  }
}
