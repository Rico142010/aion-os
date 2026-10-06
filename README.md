const state = {
  token: localStorage.getItem('aion-token') || '',
  user: null,
  projects: [],
  tasks: [],
};

const authShell = document.getElementById('auth-shell');
const appShell = document.getElementById('app-shell');
const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');
const loginMessage = document.getElementById('login-message');
const logoutButton = document.getElementById('logout-button');
const projectForm = document.getElementById('project-form');
const taskForm = document.getElementById('task-form');
const taskProjectSelect = document.getElementById('task-project-id');
const showLoginTab = document.getElementById('show-login-tab');
const showRegisterTab = document.getElementById('show-register-tab');

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

function setAuthTab(mode) {
  const isLogin = mode === 'login';
  loginForm.classList.toggle('hidden', !isLogin);
  registerForm.classList.toggle('hidden', isLogin);
  showLoginTab.classList.toggle('active', isLogin);
  showRegisterTab.classList.toggle('active', !isLogin);
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

async function registerUser(name, email, password) {
  loginMessage.textContent = 'Creando cuenta...';
  loginMessage.className = 'login-message info';

  const result = await apiFetch('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({ name, email, password }),
  });

  state.token = result.token;
  state.user = result.user;
  localStorage.setItem('aion-token', state.token);

  loginMessage.textContent = 'Cuenta creada correctamente';
  loginMessage.className = 'login-message success';
  await loadDashboard();
}

function renderProjectOptions() {
  taskProjectSelect.innerHTML = '<option value="">Selecciona un proyecto</option>' +
    state.projects
      .map((project) => `<option value="${project.id}">${project.name}</option>`)
      .join('');
}

function renderLists() {
  const projectList = document.getElementById('project-list');
  const taskList = document.getElementById('task-list');

  projectList.innerHTML = state.projects
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

  taskList.innerHTML = state.tasks
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

  renderProjectOptions();
}

async function loadDashboard() {
  const overview = await apiFetch('/api/dashboard/overview');

  state.projects = overview.projects || [];
  state.tasks = overview.tasks || [];

  document.getElementById('user-name').textContent = overview.user.name;
  document.getElementById('projects-count').textContent = overview.stats.projects;
  document.getElementById('tasks-count').textContent = overview.stats.tasks;
  document.getElementById('completed-count').textContent = overview.stats.completed;
  document.getElementById('progress-percent').textContent = `${overview.stats.progress}%`;

  renderLists();
  authShell.classList.add('hidden');
  appShell.classList.remove('hidden');
}

async function createProject(event) {
  event.preventDefault();

  const name = document.getElementById('project-name').value.trim();
  const description = document.getElementById('project-description').value.trim();
  if (!name) return;

  const project = await apiFetch('/api/projects', {
    method: 'POST',
    body: JSON.stringify({ name, description, status: 'planning' }),
  });

  state.projects.push(project);
  document.getElementById('project-form').reset();
  renderLists();
}

async function createTask(event) {
  event.preventDefault();

  const title = document.getElementById('task-title').value.trim();
  const description = document.getElementById('task-description').value.trim();
  const projectId = taskProjectSelect.value;

  if (!title || !projectId) return;

  const task = await apiFetch('/api/tasks', {
    method: 'POST',
    body: JSON.stringify({ title, description, status: 'todo', project_id: projectId }),
  });

  state.tasks.push(task);
  document.getElementById('task-form').reset();
  renderLists();
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

registerForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const name = document.getElementById('register-name').value.trim();
  const email = document.getElementById('register-email').value.trim();
  const password = document.getElementById('register-password').value.trim();

  try {
    await registerUser(name, email, password);
  } catch (error) {
    loginMessage.textContent = error.message;
    loginMessage.className = 'login-message error';
  }
});

projectForm.addEventListener('submit', createProject);
taskForm.addEventListener('submit', createTask);
showLoginTab.addEventListener('click', () => setAuthTab('login'));
showRegisterTab.addEventListener('click', () => setAuthTab('register'));

logoutButton.addEventListener('click', () => {
  localStorage.removeItem('aion-token');
  state.token = '';
  state.user = null;
  state.projects = [];
  state.tasks = [];

  authShell.classList.remove('hidden');
  appShell.classList.add('hidden');
  loginMessage.textContent = 'Sesión cerrada';
  loginMessage.className = 'login-message info';
});

setAuthTab('login');
bootstrap();
