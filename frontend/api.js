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