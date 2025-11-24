// static/main.js (обновлённая версия)

let isProcessing = false;

// === Локализация ===

const translations = {
    ru: {
        welcome: "Привет! Я могу отвечать на вопросы по вашим документам.\nСначала загрузите файлы (PDF, DOCX, TXT, MD), а затем задавайте вопросы.",
        placeholder: "Введите ваш вопрос...",
        uploadLabel: "Загрузить файлы",
        uploadStatusNoFiles: "Выберите файлы для загрузки",
        uploadStatusUploading: "Загрузка...",
        uploadSuccess: (count, errors) => `✅ Загружено: ${count} файл(ов).${errors ? ` Ошибки: ${errors}` : ''}`,
        uploadError: (msg) => `❌ ${msg || 'Неизвестная ошибка'}`,
        networkError: (msg) => `❌ Ошибка сети: ${msg}`,
        typing: "ИИ печатает",
        sources: "Источники:",
        clearChat: "Очистить чат",
        noAnswer: "❌ Не удалось получить ответ. Проверьте, запущен ли сервер и Ollama.",
        uploading: "Загрузка",
        files: "файлов",
        tempLabel: "Температура ИИ:",
    },
    en: {
        welcome: "Hi! I can answer questions about your documents.\nFirst, upload files (PDF, DOCX, TXT, MD), then ask questions.",
        placeholder: "Enter your question...",
        uploadLabel: "Upload files",
        uploadStatusNoFiles: "Please select files to upload",
        uploadStatusUploading: "Uploading...",
        uploadSuccess: (count, errors) => `✅ Uploaded: ${count} file(s).${errors ? ` Errors: ${errors}` : ''}`,
        uploadError: (msg) => `❌ ${msg || 'Unknown error'}`,
        networkError: (msg) => `❌ Network error: ${msg}`,
        typing: "AI is typing",
        sources: "Sources:",
        clearChat: "Clear chat",
        noAnswer: "❌ Failed to get a response. Please check if the server and Ollama are running.",
        uploading: "Uploading",
        files: "files",
        tempLabel: "AI Temperature:",
    }
};

let currentLang = 'ru';

function getSavedLanguage() {
    return localStorage.getItem('localmind-lang') || 'ru';
}

function setLanguage(lang) {
    if (!translations[lang]) return;
    currentLang = lang;
    localStorage.setItem('localmind-lang', lang);
    document.getElementById('languageSelect').value = lang;
    updateUIText();
}

function t(key, ...args) {
    const text = translations[currentLang][key];
    if (typeof text === 'function') {
        return text(...args);
    }
    return text;
}

function updateUIText() {
    // Кнопки и плейсхолдеры
    document.getElementById('userInput').placeholder = t('placeholder');
    document.getElementById('uploadBtn').textContent = t('uploadLabel');
    document.getElementById('clearBtn').textContent = t('clearChat');
    document.getElementById('tempLabel').textContent = t('tempLabel');
    
    // Приветственное сообщение (если чат пуст)
    const messages = document.getElementById('chat-messages');
    if (messages.children.length === 1 && !document.getElementById('typing-indicator')) {
        const welcomeMsg = messages.querySelector('.message-content');
        if (welcomeMsg) {
            welcomeMsg.innerHTML = t('welcome').replace(/\n/g, '<br>');
        }
    }
}

// === Управление темой ===

function getPreferredTheme() {
    const saved = localStorage.getItem('localmind-theme');
    if (saved) return saved;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('localmind-theme', theme);
}

// Инициализация темы при загрузке
document.addEventListener('DOMContentLoaded', () => {
    // Тема
    const currentTheme = getPreferredTheme();
    setTheme(currentTheme);
    
    // Язык
    currentLang = getSavedLanguage();
    setLanguage(currentLang);
    
    // Обработчики
    document.getElementById('themeToggle')?.addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-theme');
        const newTheme = current === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
    });
    
    document.getElementById('languageSelect')?.addEventListener('change', (e) => {
        setLanguage(e.target.value);
    });
    
    const savedTemp = localStorage.getItem('localmind-temperature') || '0.3';
    document.getElementById('tempSelect').value = savedTemp;
    
    document.getElementById('tempSelect').addEventListener('change', (e) => {
        localStorage.setItem('localmind-temperature', e.target.value);
    });
});

// === Вспомогательные функции ===

function addMessage(text, sender) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', sender);
    
    const contentDiv = document.createElement('div');
    contentDiv.classList.add('message-content');
    contentDiv.textContent = text;
    
    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function addAIResponse(text, sources = null) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', 'assistant');
    
    const contentDiv = document.createElement('div');
    contentDiv.classList.add('message-content');
    contentDiv.innerHTML = text.replace(/\n/g, '<br>');
    
    messageDiv.appendChild(contentDiv);
    
    if (sources && sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.classList.add('sources');
        sourcesDiv.innerHTML = `<strong>${t('sources')}</strong> ${sources.join(', ')}`;
        messageDiv.appendChild(sourcesDiv);
    }
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showTypingIndicator() {
    const messagesContainer = document.getElementById('chat-messages');
    const indicator = document.createElement('div');
    indicator.id = 'typing-indicator';
    indicator.classList.add('typing-indicator');
    indicator.innerHTML = `${t('typing')} <span></span><span></span><span></span>`;
    messagesContainer.appendChild(indicator);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function hideTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) indicator.remove();
}

function clearChat() {
    const messagesContainer = document.getElementById('chat-messages');
    messagesContainer.innerHTML = `
        <div class="message assistant">
            <div class="message-content">
                ${t('welcome').replace(/\n/g, '<br>')}
            </div>
        </div>
    `;
}

// === Основные функции ===

async function uploadFiles() {
    const fileInput = document.getElementById('fileInput');
    const files = Array.from(fileInput.files);
    const status = document.getElementById('uploadStatus');

    if (files.length === 0) {
        status.textContent = t('uploadStatusNoFiles');
        return;
    }

    const formData = new FormData();
    files.forEach(file => formData.append('files', file));

    status.textContent = t('uploadStatusUploading');
    try {
        const res = await fetch('/upload', { method: 'POST', body: formData });
        const data = await res.json();
        if (res.ok) {
            const successCount = data.success_count || 0;
            const errorMsg = data.errors ? ` Ошибки: ${data.errors.join(', ')}` : '';
            status.textContent = t('uploadSuccess', successCount, data.errors ? data.errors.join(', ') : '');
            fileInput.value = '';
        } else {
            status.textContent = t('uploadError', data.detail);
        }
    } catch (e) {
        status.textContent = t('networkError', e.message);
    }
}

async function sendQuestion() {
    const input = document.getElementById('userInput');
    const question = input.value.trim();
    const sendBtn = document.getElementById('sendBtn');
    const temperature = parseFloat(document.getElementById('tempSelect').value);

    if (!question || isProcessing) return;

    addMessage(question, 'user');
    input.value = '';
    input.style.height = 'auto';
    sendBtn.disabled = true;
    isProcessing = true;

    showTypingIndicator();

    try {
        // Отправляем ТОЛЬКО вопрос и температуру (без истории!)
        const res = await fetch('/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: question,
                temperature: temperature
            })
        });
        const data = await res.json();
        hideTypingIndicator();
        addAIResponse(data.answer, data.sources);
    } catch (e) {
        hideTypingIndicator();
        addAIResponse("❌ Не удалось получить ответ. Проверьте, запущен ли сервер и Ollama.");
    } finally {
        sendBtn.disabled = false;
        isProcessing = false;
    }
}

// === Инициализация ===

document.getElementById('userInput').addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});

document.getElementById('uploadBtn').addEventListener('click', uploadFiles);
document.getElementById('sendBtn').addEventListener('click', sendQuestion);
document.getElementById('clearBtn').addEventListener('click', clearChat);

document.getElementById('userInput').addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
        sendQuestion();
    }
});