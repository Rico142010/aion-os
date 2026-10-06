async function loadHealth() {
  const statusEl = document.getElementById('status');
  const apiStatus = document.getElementById('api-status');
  const envStatus = document.getElementById('env-status');

  try {
    const response = await fetch('/api/health');
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Error de conexión');
    }

    const isReady = data.status === 'ok';
    statusEl.textContent = isReady ? 'Sistema operativo' : 'Sistema degradado';
    statusEl.className = isReady ? 'status-pill success' : 'status-pill loading';
    apiStatus.textContent = data.database?.ok && data.redis?.ok ? 'OK' : 'WARN';
    envStatus.textContent = data.env || 'development';
  } catch (error) {
    statusEl.textContent = 'Sin conexión';
    statusEl.className = 'status-pill loading';
    apiStatus.textContent = 'ERROR';
    envStatus.textContent = 'offline';
    console.error(error);
  }
}

loadHealth();
