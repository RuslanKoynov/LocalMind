# LocalMind — Local AI Tool for Knowledge Base Interaction

**LocalMind** is an offline AI-powered tool that lets you upload local documents (PDF, DOCX, TXT, Markdown), index them, and ask natural language questions. All processing happens **entirely offline**, with no data sent to the cloud.

---

## 📦 Installation

### Requirements
- OS: Windows, macOS, or Linux  
- Python 3.10 or newer  
- [Ollama](https://ollama.com/) — to run the large language model (LLM)  
- At least 4 GB RAM (8 GB+ recommended for larger models)

### Steps

1. **Install Python** (if not already installed):  
   [https://www.python.org/downloads/](https://www.python.org/downloads/)

2. **Install Ollama**:  
   Follow the instructions at [https://ollama.com/](https://ollama.com/)

3. **Download the project** (or clone the repository):
   ```bash
   git clone https://github.com/RuslanKoynov/LocalMind.git
   cd localmind
   ```

4. **Install Python dependencies**:
   ```bash
   pip install streamlit chromadb sentence-transformers PyPDF2 python-docx networkx torchvision requests
   ```

5. **Pull a language model into Ollama** (choose one):

   For best Russian language support:
   ```bash
   ollama pull qwen2.5:1.5b
   ```

   Or a lighter option (works well on low-end machines):
   ```bash
   ollama pull phi3:mini
   ```

---

## ⚙️ Configuration

### Optional Settings

You can change the LLM models directly in the application sidebar:
- **Chat Model**: Used to generate the final answer.
- **Graph Model**: Used to extract entities and relationships for the knowledge graph. (For better results, use a more capable model like `qwen2.5` or `llama3`).

### Project Directories

- `documents/` — stores original uploaded files (created automatically)  
- `chroma_db/` — local vector knowledge base (created automatically)  
- `knowledge_graph.json` — local knowledge graph (created automatically)

> All data remains on your device and **never leaves your system**.

---

## 🚀 Usage

### 1. Start the Application

In your terminal, navigate to the project folder and run:

```bash
streamlit run app.py
```

### 2. Upload Documents

- Supported formats: `.txt`, `.md`, `.pdf`, `.docx`  
- You can upload **one or multiple files at once**  
- Files are automatically indexed into both the **Vector Database** and the **Knowledge Graph**.

### 3. Ask Questions

- Type your question in the chat input field  
- The AI uses a **Hybrid RAG (Vector + Graph)** approach:
    - **Vector Search**: Finds the most relevant text chunks.
    - **Graph Expansion**: Finds related entities and connections to provide a broader context.
- The AI returns an answer **with source references**.

### 4. Example Queries

- “What are the system installation requirements?”  
- “Who is the author of the ‘User Guide’ document?”  
- “Who is Tatyana Larina?” (if you’ve uploaded *Eugene Onegin*)

---

## 🔐 Privacy & Security

- All computation happens **locally on your machine**  
- No data is transmitted over the internet (after initial model download)  
- The vector database and knowledge graph are stored on your local disk  

---

## 🛠 Troubleshooting

| Issue | Solution |
|------|----------|
| “Generation error” | Ensure Ollama is running and the model is loaded (`ollama list`) |
| PDF files fail to upload | Make sure the PDF contains selectable text (not a scanned image) |
| Slow first launch | The embedding model downloads on first run (internet required once) |

---

## 📁 Project Structure

```
localmind/
├── app.py                     # Main application (Streamlit UI)
├── graph_manager.py           # Knowledge Graph logic (NetworkX)
├── LocalMindBox.exe           # Legacy backend (Executable Windows file)
├── documents/                 # Uploaded files
├── chroma_db/                # Vector knowledge base
└── knowledge_graph.json        # Serialized knowledge graph
```

---

> 💡 **Tip**: For large document collections, use an SSD and at least 8 GB of RAM.

---

**LocalMind — your private AI assistant for knowledge, fully under your control.**
