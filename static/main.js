// static/main.js

async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const files = Array.from(fileInput.files); // Превращаем FileList в массив
    const status = document.getElementById('uploadStatus');

    if (files.length === 0) {
        status.textContent = "Выберите один или несколько файлов.";
        return;
    }

    const formData = new FormData();
    files.forEach(file => {
        formData.append('files', file); // Ключ 'files' — массив
    });

    status.textContent = `Загрузка ${files.length} файла(ов)...`;
    try {
        const res = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (res.ok) {
            const successCount = data.success_count || 0;
            const errorFiles = data.errors ? data.errors.join(', ') : '';
            let msg = `✅ Успешно загружено файлов: ${successCount}`;
            if (errorFiles) {
                msg += ` | Ошибки: ${errorFiles}`;
            }
            status.textContent = msg;
            fileInput.value = ''; // Сброс выбора
        } else {
            status.textContent = `❌ Ошибка: ${data.detail || 'Неизвестно'}`;
        }
    } catch (e) {
        status.textContent = `❌ Сетевая ошибка: ${e.message}`;
    }
}

async function askQuestion() {
    const question = document.getElementById('question').value.trim();
    const resultDiv = document.getElementById('result');
    if (!question) {
        alert('Введите вопрос');
        return;
    }

    resultDiv.style.display = 'block';
    resultDiv.innerHTML = '<p>Думаю... (это может занять 10–30 секунд)</p>';

    try {
        const res = await fetch('/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `question=${encodeURIComponent(question)}`
        });
        const data = await res.json();
        let html = `<h3>Ответ:</h3><p>${data.answer.replace(/\n/g, '<br>')}</p>`;
        if (data.sources) {
            html += `<div class="sources"><strong>Источники:</strong> ${data.sources.join(', ')}</div>`;
        }
        resultDiv.innerHTML = html;
    } catch (e) {
        resultDiv.innerHTML = `<p>❌ Ошибка: ${e.message}</p>`;
    }
}