# LocalMind — Local AI Tool for Knowledge Base Interaction

**LocalMind** is an offline AI-powered tool that lets you upload local documents (PDF, DOCX, TXT, Markdown), index them, and ask natural language questions. All processing happens **entirely offline**, with no data sent to the cloud.

---

## 📦 Installation

### Requirements
- OS: Windows
- [Ollama](https://ollama.com/) — to run the large language model (LLM)  
- At least 4 GB RAM (8 GB+ recommended for larger models)

### Steps

1. **Download the project** (or clone the repository):
   ```bash
   git clone https://github.com/RuslanKoynov/LocalMind.git
   cd localmind
   ```

2. **Install Ollama**:  
   Follow the instructions at [https://ollama.com/](https://ollama.com/)

3. **Pull a language model into Ollama** (choose one):

   For best Russian language support:
   ```bash
   ollama pull qwen2.5:1.5b
   ```

   Or a lighter option (works well on low-end machines):
   ```bash
   ollama pull phi3:mini
   ```

---

## 🚀 Usage

### 1. Start the Server

Run LocalMindBox.exe

The application will be available at:  
👉 [http://127.0.0.1:8000](http://127.0.0.1:8000)

### 2. Upload Documents

- Supported formats: `.txt`, `.md`, `.pdf`, `.docx`  
- You can upload **one or multiple files at once**  
- Files are automatically indexed after upload (may take a few seconds)

### 3. Ask Questions

- Type your question in the “Ask a question” field  
- The AI analyzes your documents and returns an answer **with source references**  
- If the answer isn’t found in your documents, the system will let you know

### 4. Example Queries

- “What are the system installation requirements?”  
- “Who is the author of the ‘User Guide’ document?”  
- “List the setup steps for module X.”  
- “Who is Tatyana Larina?” (if you’ve uploaded *Eugene Onegin*)

### 5. AI Temperature Setting

The higher the value, the more "imagination" (or creativity) the AI will use in its responses. For text-based document search, a value of 0.3 is usually sufficient.

---

## 🔐 Privacy & Security

- All computation happens **locally on your machine**  
- No data is transmitted over the internet (after initial model download)  
- The vector database is stored on your local disk  
- Safe for use in corporate environments with strict data policies

---

## 🛠 Troubleshooting

| Issue | Solution |
|------|----------|
| “Generation error” | Ensure Ollama is running and the model is loaded (`ollama list`) |
| PDF files fail to upload | Make sure the PDF contains selectable text (not a scanned image) |
| Slow first launch | The embedding model downloads on first run (internet required once) |
| Server fails to start | Contact me, will try to help 😎 |

---

> 💡 **Tip**: For large document collections, use an SSD and at least 8 GB of RAM.

---

**LocalMind — your private AI assistant for knowledge, fully under your control.**
