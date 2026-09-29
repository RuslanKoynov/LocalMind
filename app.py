import streamlit as st
import os
import uuid
import re
import chromadb
from sentence_transformers import SentenceTransformer
from PyPDF2 import PdfReader
from docx import Document
import requests
from typing import List
from graph_manager import GraphManager

# === Настройки ===
DOC_DIR = "./documents"
CHROMA_DIR = "./chroma_db"
os.makedirs(DOC_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)

st.set_page_config(page_title="LocalMind AI", page_icon="🧠🤖 ", layout="wide")

# === Кэширование моделей и БД ===
@st.cache_resource
def init_resources():
    # Эмбеддинг-модель
    embedding_model = SentenceTransformer('intfloat/multilingual-e5-base')
    # Векторная БД
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_or_create_collection(name="docs", embedding_function=None)
    # Граф знаний
    gm = GraphManager()
    gm.load_graph("knowledge_graph.json")
    return embedding_model, collection, gm

embedding_model, collection, gm = init_resources()

# === Вспомогательные функции ===
def chunk_text(text: str, chunk_size: int = 512) -> List[str]:
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
            text = "".join([page.extract_text() or "" for page in reader.pages])
            return text
        elif ext == '.docx':
            doc = Document(filepath)
            return "\n".join([p.text for p in doc.paragraphs])
        elif ext in ('.txt', '.md'):
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        return ""
    except Exception as e:
        st.error(f"Ошибка извлечения текста из {filepath}: {e}")
        return ""

def ask_ollama(prompt: str, temperature: float = 0.2, model: str = "phi4-mini:latest") -> str:
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature}
            },
            timeout=120
        )
        if response.status_code != 200:
            return f"Ollama error {response.status_code}: {response.text}"
        return response.json().get("response", "").strip()
    except Exception as e:
        return f"Ошибка запроса к Ollama: {str(e)}"

# === Интерфейс Streamlit ===
st.title("🧠🤖  LocalMind AI")
st.markdown("Ваша приватная база знаний. Все данные остаются локально.")

# Боковая панель настроек
with st.sidebar:
    st.header("⚙️ Настройки")
    llm_model = st.text_input("Модель Ollama (Чат)", value="phi4-mini:latest")
    graph_model = st.text_input("Модель Ollama (Граф)", value="phi4-mini:latest")
    temp = st.slider("Температура", 0.0, 1.0, 0.3)
    
    # Обновляем модель в менеджере графа, если она изменилась
    gm.set_model(graph_model)
    
    st.divider()
    st.subheader("📁 Документы")
    uploaded_files = st.file_uploader("Загрузить файлы", type=['pdf', 'docx', 'txt', 'md'], accept_multiple_files=True)
    
    if st.button("Индексировать файлы"):
        if uploaded_files:
            with st.spinner("Обработка документов..."):
                success_count = 0
                for uploaded_file in uploaded_files:
                    ext = os.path.splitext(uploaded_file.name)[1].lower()
                    safe_filename = f"{uuid.uuid4().hex}{ext}"
                    filepath = os.path.join(DOC_DIR, safe_filename)
                    
                    with open(filepath, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    text = extract_text_from_file(filepath, ext)
                    if text.strip():
                        # Добавление в векторную БД
                        chunks = chunk_text(text)
                        embeddings = embedding_model.encode(chunks).tolist()
                        ids = [str(uuid.uuid4()) for _ in chunks]
                        metadatas = [{"source": uploaded_file.name} for _ in chunks]
                        
                        collection.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
                        
                        # Добавление в граф знаний (по чанкам, чтобы не перегружать LLM)
                        for chunk in chunks:
                            gm.add_text_to_graph(chunk)
                        gm.save_graph("knowledge_graph.json")
                        
                        success_count += 1
                st.success(f"Успешно индексировано файлов: {success_count}")
        else:
            st.warning("Сначала выберите файлы")

# Основная область чата
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Задайте вопрос по вашим документам..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Поиск в базе знаний..."):
            # Поиск в ChromaDB
            query_emb = embedding_model.encode([prompt]).tolist()[0]
            search_results = collection.query(query_embeddings=[query_emb], n_results=3)
            
            docs = search_results['documents'][0] if search_results['documents'] else []
            metas = search_results['metadatas'][0] if search_results['metadatas'] else []
            
            # Расширение контекста через граф
            graph_context = ""
            if docs:
                # Извлекаем ключевые сущности из первого (самого релевантного) документа
                # Для простоты берем первые несколько существительных или просто просим LLM выделить сущности
                entity_extraction_prompt = f"Extract the main entity (person, organization, concept) from this text in 1-3 words: {docs[0]}"
                main_entity = ask_ollama(entity_extraction_prompt, 0.1, llm_model)
                if main_entity:
                    graph_context = gm.get_related_context(main_entity)
            
            if not docs and not graph_context:
                answer = "В базе знаний нет подходящей информации."
            else:
                context = "\n\n".join([f"[Источник: {m['source']}]\n{d}" for d, m in zip(docs, metas)])
                if graph_context:
                    context += f"\n\n[Связи из графа знаний]:\n{graph_context}"
                
                full_prompt = f"""Ты — специалист по поиску информации в документации. Твоя задача — дать точный и четкий ответ на вопрос пользователя, используя ТОЛЬКО предоставленный контекст.
                
                Правила:
                1. Если ответ есть в контексте — дай его, указав источник.
                2. Если информации недостаточно — скажи, что именно отсутствует.
                3. Если ответа нет вообще — сообщи: «В предоставленной документации эта информация не найдена».
                4. Запрещено использовать свои знания вне контекста.
                
                Контекст:
                {context}
                
                Вопрос: {prompt}
                
                Ответ:"""
                answer = ask_ollama(full_prompt, temp, llm_model)
            
            st.markdown(answer)
            if docs:
                with st.expander("Посмотреть источники"):
                    for d, m in zip(docs, metas):
                        st.info(f"**{m['source']}**: {d}")
            
            st.session_state.messages.append({"role": "assistant", "content": answer})
