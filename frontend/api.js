// api.js - Полноценная версия для работы с бэкендом FastAPI
const API_BASE_URL = 'http://localhost:8000';

class ApiClient {
    constructor() {
        this.baseURL = API_BASE_URL;
        this.token = localStorage.getItem('access_token');
    }

    getToken() {
        return localStorage.getItem('access_token');
    }

    setToken(token) {
        if (token) {
            localStorage.setItem('access_token', token);
            this.token = token;
        } else {
            localStorage.removeItem('access_token');
            this.token = null;
        }
    }

    async request(endpoint, options = {}) {
        const token = this.getToken();
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                ...options,
                headers
            });

            // Для 204 No Content
            if (response.status === 204) {
                return null;
            }

            // Пытаемся получить JSON ответ
            let data;
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
            } else {
                data = await response.text();
            }

            if (!response.ok) {
                const errorMessage = data?.detail || data?.message || `HTTP ${response.status}: ${response.statusText}`;
                throw new Error(errorMessage);
            }

            return data;
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    }

    // ========== АВТОРИЗАЦИЯ ==========
    
    async register(userData) {
        const response = await this.request('/register', {
            method: 'POST',
            body: JSON.stringify({
                name: userData.name,
                email: userData.email,
                password: userData.password,
                preferred_role: userData.preferred_role || 'Не выбрана'
            })
        });
        return response;
    }

    async login(credentials) {
        const response = await this.request('/login', {
            method: 'POST',
            body: JSON.stringify({
                email: credentials.email,
                password: credentials.password
            })
        });
        
        if (response && response.access_token) {
            this.setToken(response.access_token);
        }
        
        return response;
    }

    async getCurrentUser() {
        const response = await this.request('/user/me');
        return response;
    }

    async logout() {
        this.setToken(null);
    }

    // ========== ЧАТЫ ==========

    async getUserChats() {
        const response = await this.request('/chats');
        return response || [];
    }

    async createChat(title, role) {
        const response = await this.request('/chats', {
            method: 'POST',
            body: JSON.stringify({
                title: title,
                role: role || 'Не выбрана'
            })
        });
        return response;
    }

    async getChatMessages(chatId) {
        const response = await this.request(`/chats/${chatId}/messages`);
        return response || [];
    }

    async saveMessage(chatId, message, isUser = true) {
        const response = await this.request(`/chats/${chatId}/messages`, {
            method: 'POST',
            body: JSON.stringify({
                user_message: message
            })
        });
        return response;
    }

    async sendMessageWithChat(chatId, userMessage, roleName) {
        const response = await this.request('/chat', {
            method: 'POST',
            body: JSON.stringify({
                user_message: userMessage,
                role_name: roleName || 'Не выбрана',
                chat_id: chatId ? parseInt(chatId) : null
            })
        });
        return response;
    }

    // ========== НАСТРОЕНИЕ ==========

    async logMood(moodValue) {
        const response = await this.request('/mood/log', {
            method: 'POST',
            body: JSON.stringify({
                mood_value: moodValue
            })
        });
        return response;
    }

    // ========== УДАЛЕНИЕ АККАУНТА ==========

    async deleteAccount() {
        const response = await this.request('/user/me', {
            method: 'DELETE'
        });
        return response;
    }
}

// Создаем глобальный экземпляр API
const api = new ApiClient();
