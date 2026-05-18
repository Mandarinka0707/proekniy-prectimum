<<<<<<< HEAD
// Локальный режим: без бэкенда, всё в localStorage браузера
const LOCAL_USER_KEY = 'heartmind:localUser';
const CHATS_KEY = 'heartmind:chatList';
const MESSAGES_KEY = 'heartmind:chatMessages';

const AI_REPLIES = [
  'Спасибо, что поделились. Давайте разберём ситуацию шаг за шагом — что для вас сейчас самое важное?',
  'Я слышу вас. Расскажите подробнее: что именно вызывает сильные эмоции в этой ситуации?',
  'Понимаю, это непросто. Какие мысли чаще всего приходят вам в голову, когда вы об этом думаете?',
  'Хороший вопрос. Что бы вы хотели изменить в этой ситуации в первую очередь?',
];

class ApiClient {
  constructor() {
    this.token = localStorage.getItem('access_token');
  }

  
  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem('access_token', token);
    } else {
      localStorage.removeItem('access_token');
    }
  }

  _getUser() {
    try {
      const raw = localStorage.getItem(LOCAL_USER_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }

  _readChats() {
    try {
      const raw = localStorage.getItem(CHATS_KEY);
      const parsed = raw ? JSON.parse(raw) : [];
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }

  _writeChats(chats) {
    localStorage.setItem(CHATS_KEY, JSON.stringify(chats));
  }

  _readMessagesMap() {
    try {
      const raw = localStorage.getItem(MESSAGES_KEY);
      const parsed = raw ? JSON.parse(raw) : {};
      return parsed && typeof parsed === 'object' ? parsed : {};
    } catch {
      return {};
    }
  }

  _writeMessagesMap(map) {
    localStorage.setItem(MESSAGES_KEY, JSON.stringify(map));
  }

  _chatKey(chatId) {
    return String(chatId);
  }

  async register(userData) {
    const email = (userData.email || '').trim().toLowerCase();
    const existing = this._getUser();

    if (existing && existing.email === email) {
      throw new Error('Пользователь с таким email уже зарегистрирован');
    }

    localStorage.setItem(
      LOCAL_USER_KEY,
      JSON.stringify({
        name: (userData.name || '').trim(),
        email,
        password: userData.password,
        preferred_role: userData.preferred_role || 'Не выбрана',
      }),
    );

    return { ok: true };
  }

  async login(credentials) {
    const email = (credentials.email || '').trim().toLowerCase();
    const user = this._getUser();

    if (!user) {
      throw new Error('Аккаунт не найден. Сначала зарегистрируйтесь.');
    }

    if (user.email !== email || user.password !== credentials.password) {
      throw new Error('Неверный email или пароль');
    }

    this.setToken('local-session');
    return { access_token: 'local-session' };
  }

  async getCurrentUser() {
    const user = this._getUser();
    if (!user) {
      throw new Error('Необходимо авторизоваться');
    }

    return {
      name: user.name,
      email: user.email,
      preferred_role: user.preferred_role,
    };
  }

  async getUserChats() {
    return this._readChats().map((chat) => ({
      id: chat.id,
      title: chat.title,
    }));
  }

  async createChat(title, role) {
    const chats = this._readChats();
    const newChat = {
      id: String(Date.now()),
      title: title || `Новый чат ${chats.length + 1}`,
      role: role || 'Не выбрана',
    };

    const updated = [newChat, ...chats];
    this._writeChats(updated);

    const messagesMap = this._readMessagesMap();
    messagesMap[newChat.id] = [];
    this._writeMessagesMap(messagesMap);

    return { id: newChat.id, title: newChat.title };
  }

  async getChatMessages(chatId) {
    const key = this._chatKey(chatId);
    const messages = this._readMessagesMap()[key] || [];

    return messages.map((msg) => ({
      is_user: msg.author === 'user',
      message: msg.text,
    }));
  }

  async saveMessage(chatId, message, isUser = true) {
    const key = this._chatKey(chatId);
    const messagesMap = this._readMessagesMap();
    const list = messagesMap[key] || [];
    const author = isUser ? 'user' : 'assistant';
    const last = list[list.length - 1];

    if (last && last.text === message && last.author === author) {
      return { ok: true };
    }

    list.push({ author, text: message });
    messagesMap[key] = list;
    this._writeMessagesMap(messagesMap);

    return { ok: true };
  }

  async sendMessage(message, roleName) {
    return this.sendMessageWithChat(null, message, roleName);
  }

  async sendMessageWithChat(chatId, message, roleName) {
    const role = roleName || 'Не выбрана';
    const reply =
      AI_REPLIES[Math.floor(Math.random() * AI_REPLIES.length)] +
      (role !== 'Не выбрана' ? ` (роль: ${role})` : '');

    return { reply };
  }

  async logMood(moodValue) {
    localStorage.setItem('heartmind:currentMood', moodValue);
    return { ok: true };
  }
}

const api = new ApiClient();
=======
// api.js
const API_BASE_URL = 'http://localhost:8000';

class ApiClient {
    constructor() {
        this.token = localStorage.getItem('access_token');
    }

    setToken(token) {
        this.token = token;
        if (token) {
            localStorage.setItem('access_token', token);
        } else {
            localStorage.removeItem('access_token');
        }
    }

    getHeaders() {
        const headers = {
            'Content-Type': 'application/json',
        };
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        return headers;
    }

    async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        try {
            const response = await fetch(url, {
                ...options,
                headers: this.getHeaders(),
            });

            if (response.status === 401) {
                this.setToken(null);
                if (!window.location.pathname.includes('login.html') && 
                    !window.location.pathname.includes('register.html')) {
                    window.location.href = 'login.html';
                }
                throw new Error('Необходимо авторизоваться');
            }

            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: 'Ошибка запроса' }));
                throw new Error(error.detail || 'Ошибка запроса');
            }

            if (response.status === 204) {
                return null;
            }

            return response.json();
        } catch (error) {
            if (error.message === 'Failed to fetch') {
                throw new Error('Не удается подключиться к серверу. Убедитесь, что бэкенд запущен.');
            }
            throw error;
        }
    }

    async register(userData) {
        return this.request('/register', {
            method: 'POST',
            body: JSON.stringify(userData),
        });
    }

    async login(credentials) {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(credentials),
        });
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Ошибка входа' }));
            throw new Error(error.detail || 'Ошибка входа');
        }
        
        const data = await response.json();
        this.setToken(data.access_token);
        return data;
    }

    async sendMessage(message, roleName) {
        return this.request('/chat', {
            method: 'POST',
            body: JSON.stringify({
                user_message: message,
                role_name: roleName,
            }),
        });
    }

    async logMood(moodValue) {
        return this.request('/mood/log', {
            method: 'POST',
            body: JSON.stringify({
                mood_value: moodValue,
            }),
        });
    }

    async getCurrentUser() {
        return this.request('/user/me');
    }

     async getUserChats() {
        return this.request('/chats');
    }

    async createChat(title, role) {
        return this.request('/chats', {
            method: 'POST',
            body: JSON.stringify({ title, role })
        });
    }

    async getChatMessages(chatId) {
        return this.request(`/chats/${chatId}/messages`);
    }

    async saveMessage(chatId, message) {
        return this.request(`/chats/${chatId}/messages`, {
            method: 'POST',
            body: JSON.stringify({ user_message: message, role_name: '' })
        });
    }

    async sendMessageWithChat(chatId, message, roleName) {
        return this.request('/chat', {
            method: 'POST',
            body: JSON.stringify({
                user_message: message,
                role_name: roleName,
                chat_id: chatId  // Добавьте chat_id в запрос
            })
        });
    }
}

const api = new ApiClient();
>>>>>>> 134c47470fddace47a538c4202de3ca1e95b5f1d
