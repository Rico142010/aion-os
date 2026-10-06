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

    statusEl.textContent = 'Sistema operativo';
    statusEl.className = 'status-pill success';
    apiStatus.textContent = 'OK';
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
