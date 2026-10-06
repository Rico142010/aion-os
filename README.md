const state = {
  token: localStorage.getItem('aion-token') || '',
  user: null,
};

const authShell = document.getElementById('auth-shell');
const appShell = document.getElementById('app-shell');
const loginForm = document.getElementById('login-form');
const loginMessage = document.getElementById('login-message');
const logoutButton = document.getElementById('logout-button');

async function apiFetch(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }

  const response = await fetch(path, {
    ...options,
    headers,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || 'No se pudo completar la solicitud');
  }

  return data;
}

async function loginUser(email, password) {
  loginMessage.textContent = 'Iniciando sesión...';
  loginMessage.className = 'login-message info';

  const result = await apiFetch('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });

  state.token = result.token;
  state.user = result.user;
  localStorage.setItem('aion-token', state.token);

  loginMessage.textContent = 'Sesión iniciada correctamente';
  loginMessage.className = 'login-message success';

  await loadDashboard();
}

async function loadDashboard() {
  const overview = await apiFetch('/api/dashboard/overview');

  document.getElementById('user-name').textContent = overview.user.name;
  document.getElementById('projects-count').textContent = overview.stats.projects;
  document.getElementById('tasks-count').textContent = overview.stats.tasks;
  document.getElementById('completed-count').textContent = overview.stats.completed;
  document.getElementById('progress-percent').textContent = `${overview.stats.progress}%`;

  const projectList = document.getElementById('project-list');
  const taskList = document.getElementById('task-list');

  projectList.innerHTML = overview.projects
    .map(
      (project) => `
        <li>
          <div>
            <strong>${project.name}</strong>
            <small>${project.status}</small>
          </div>
          <span>${project.description || 'Sin descripción'}</span>
        </li>
      `
    )
    .join('');

  taskList.innerHTML = overview.tasks
    .map(
      (task) => `
        <li>
          <div>
            <strong>${task.title}</strong>
            <small>${task.status}</small>
          </div>
          <span>${task.description || 'Sin descripción'}</span>
        </li>
      `
    )
    .join('');

  authShell.classList.add('hidden');
  appShell.classList.remove('hidden');
}

async function bootstrap() {
  if (!state.token) {
    authShell.classList.remove('hidden');
    appShell.classList.add('hidden');
    return;
  }

  try {
    const user = await apiFetch('/api/auth/me');
    state.user = user;
    await loadDashboard();
  } catch (error) {
    localStorage.removeItem('aion-token');
    state.token = '';
    authShell.classList.remove('hidden');
    appShell.classList.add('hidden');
    loginMessage.textContent = 'La sesión expiró. Vuelve a iniciar sesión.';
    loginMessage.className = 'login-message warning';
  }
}

loginForm.addEventListener('submit', async (event) => {
  event.preventDefault();

  const email = document.getElementById('email-input').value.trim();
  const password = document.getElementById('password-input').value.trim();

  try {
    await loginUser(email, password);
  } catch (error) {
    loginMessage.textContent = error.message;
    loginMessage.className = 'login-message error';
  }
});

logoutButton.addEventListener('click', () => {
  localStorage.removeItem('aion-token');
  state.token = '';
  state.user = null;

  authShell.classList.remove('hidden');
  appShell.classList.add('hidden');
  loginMessage.textContent = 'Sesión cerrada';
  loginMessage.className = 'login-message info';
});

bootstrap();
