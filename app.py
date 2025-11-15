# app.py
import os
import uuid
import re
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import chromadb
from sentence_transformers import SentenceTransformer
import aiofiles
from typing import List
import requests

# PDF & DOCX
from PyPDF2 import PdfReader
from docx import Document

# === Настройки ===
DOC_DIR = "./documents"
CHROMA_DIR = "./chroma_db"
os.makedirs(DOC_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)

# === Инициализация ===
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Эмбеддинг-модель (многоязычная, в т.ч. русский)
embedding_model = SentenceTransformer('intfloat/multilingual-e5-base')

# Векторная БД
client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_or_create_collection(
    name="docs",
    embedding_function=None
)

def chunk_text(text: str, chunk_size: int = 512) -> List[str]:
    # Очистка пробелов и разбивка
    text = re.sub(r'\s+', ' ', text).strip()
    if not text:
        return []
    words = text.split()
    chunks = []
    current = []
    for word in words:
        current.append(word)
        if len(" ".join(current)) > chunk_size:
            chunks.append(" ".join(current))
            current = []
    if current:
        chunks.append(" ".join(current))
    return chunks

def extract_text_from_file(filepath: str, ext: str) -> str:
    try:
        if ext == '.pdf':
            reader = PdfReader(filepath)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        elif ext == '.docx':
            doc = Document(filepath)
            return "\n".join([p.text for p in doc.paragraphs])
        elif ext in ('.txt', '.md'):
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        else:
            raise ValueError("Unsupported format")
    except Exception as e:
        print(f"Ошибка извлечения текста из {filepath}: {e}")
        return ""

def ask_ollama(context: str, question: str, model: str = "qwen2.5:0.5b") -> str:
#def ask_ollama(context: str, question: str, model: str = "phi3:mini") -> str:
    prompt = f"""Ты — умный помощник по документации. Ответь чётко и по делу, используя ТОЛЬКО приведённый ниже контекст.
Если в контексте нет ответа, напиши: "В загруженных документах ответ не найден."

Контекст:
{context}

Вопрос: {question}

Ответ:"""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2}
            },
            timeout=120
        )
        return response.json().get("response", "Ошибка генерации.").strip()
    except Exception as e:
        return f"Ошибка: Ollama не отвечает. Запущен ли он? ({str(e)})"

# === Эндпоинты ===

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Принимает несколько файлов одновременно.
    Возвращает количество успешно обработанных файлов и список ошибок.
    """
    if not files:
        raise HTTPException(status_code=400, detail="Нет файлов для загрузки")

    success_count = 0
    errors = []

    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ('.txt', '.md', '.pdf', '.docx'):
            errors.append(f"{file.filename} (неподдерживаемый формат)")
            continue

        safe_filename = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(DOC_DIR, safe_filename)

        try:
            content = await file.read()
            async with aiofiles.open(filepath, 'wb') as f:
                await f.write(content)

            text = extract_text_from_file(filepath, ext)
            if not text.strip():
                os.remove(filepath)
                errors.append(f"{file.filename} (пустой или нечитаемый)")
                continue

            chunks = chunk_text(text)
            if not chunks:
                os.remove(filepath)
                errors.append(f"{file.filename} (не удалось разбить на фрагменты)")
                continue

            embeddings = embedding_model.encode(chunks).tolist()
            ids = [str(uuid.uuid4()) for _ in chunks]
            metadatas = [{"source": file.filename} for _ in chunks]

            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=chunks,
                metadatas=metadatas
            )

            success_count += 1

        except Exception as e:
            errors.append(f"{file.filename} (ошибка: {str(e)[:50]}...)")
            if os.path.exists(filepath):
                os.remove(filepath)

    return {
        "success_count": success_count,
        "total_files": len(files),
        "errors": errors if errors else None
    }

@app.post("/query")
async def query_knowledge(question: str = Form(...)):
    if not question.strip():
        raise HTTPException(status_code=400, detail="Вопрос не может быть пустым")
    
    results = collection.peek()
    if results['ids'] == []:
        return {"answer": "База знаний пуста. Загрузите документы."}
    
    query_emb = embedding_model.encode([question]).tolist()[0]
    search_results = collection.query(query_embeddings=[query_emb], n_results=3)
    
    docs = search_results['documents'][0]
    metas = search_results['metadatas'][0]
    
    if not docs:
        return {"answer": "Ничего не найдено."}
    
    context = "\n\n".join([f"[Источник: {m['source']}]\n{d}" for d, m in zip(docs, metas)])
    answer = ask_ollama(context, question)
    
    sources = list(set([m['source'] for m in metas]))
    
    return {
        "question": question,
        "answer": answer,
        "sources": sources
    }

# Отдаём веб-интерфейс
@app.get("/", response_class=HTMLResponse)
async def get_ui():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()