Conversational AI System – Your Local Technical Interview Coach (Qwen + llama.cpp)

Description:
This project is all about building a Conversational AI System that acts as a technical interview coach specifically for AI/ML roles. It runs locally on your computer using a quantized Qwen model powered by llama.cpp and llama-cpp-python. It includes: 
    - A FastAPI backend with both WebSocket and REST APIs
    - A ChatGPT-style web interface that streams interview questions live, as they  are generated

What makes it special?
   - It runs entirely on your CPU (no need for expensive GPUs), using a quantized GGUF model.
   - Supports real-time streaming of tokens over WebSocket to make the chat feel smooth and interactive.
   - Keeps track of each conversation independently, so your interview progress is saved per session.
   - Handles multiple users simultaneously — one WebSocket session per browser tab.
   - Clean and simple API endpoints (/api/health, /api/chat, /ws/chat) for easy integration.
   - Modern, user-friendly chat UI with topic selection and session history.

1. What’s the idea? (Phase I)
This tool is designed as a Technical Interview Coach for AI/ML engineer candidates.
   - Who’s it for? Someone prepping for AI/ML interviews.
   - What does it do? Acts like a senior technical interviewer who asks questions around AI, ML, deep learning, large language models, data science, and related math.
   - How does it behave?
      - Only asks questions on those topics.
      - Asks one focused question at a time.
      - Sticks to the user’s chosen topic (like "transformers", "CNNs", or "MLOps").
      - Adjusts question difficulty based on previous answers.

Example conversation snippet:
Topic: “transformers and attention”
Question 1: “Can you explain how self-attention works in a transformer encoder?”
Candidate answers about query/key/value and attention weights.
Question 2: “How does multi-head attention differ from single-head attention, and why is it useful?”
Candidate answers again.
Question 3: “What are some common ways to reduce the quadratic attention cost for long sequences?”

How it flows:
   - You open the web app and pick a topic.
   - The frontend starts a new WebSocket session, sends the topic to the backend.
   - The conversation manager sets up the interview and asks the first question.
   - You answer; your answer is saved in history.
   - The conversation manager assembles a prompt (system instructions + conversation history).
   - The model generates the next question, streaming it token-by-token to your screen.
   - Repeat steps 4–6 until you type exit.
   - Your entire chat is saved locally in your browser for reference.
2. How to set it up (Windows)
Create and activate a Python virtual environment in your project folder (say c:\Users\HP\Desktop\nlp):

python -m venv .venv
.venv\Scripts\activate
Install all the needed packages:

pip install -r requirements.txt
Make sure llama-cpp-python and its CPU dependencies are installed and working. It usually handles compilation automatically, but if you have trouble, check the official docs here:
https://github.com/abetlen/llama-cpp-python

3. Download and place your Qwen GGUF model
You should have your model file ready at:

c:\Users\HP\Desktop\nlp\models\ECE-Qwen0.5B-FT-V2.Q2_K.gguf
The code expects it there by default:

MODEL_PATH=models/ECE-Qwen0.5B-FT-V2.Q2_K.gguf
If you rename or move it, just update the MODEL_PATH setting accordingly.

4. Configure your model path and settings
Create a .env file in the project root folder to easily manage settings:

MODEL_PATH=models/ECE-Qwen0.5B-FT-V2.Q2_K.gguf
N_CTX=4096
N_GPU_LAYERS=0
5. Run the web app (FastAPI backend + WebSocket + UI)
From the project root with your virtual environment activated, start the server:

.\.venv\Scripts\python.exe -m uvicorn backend:app --reload
Then open your browser at: http://127.0.0.1:8000/

What you’ll see:
   - A topic selection screen first.
   - Pick a topic like “transformers and attention” and click Start interview.
   - The chat interface launches, and the AI interviewer starts streaming the first question.
   - Type your answers and hit Enter or click Send.
   - Use New session to start fresh with a new topic.
   - Your previous sessions are saved in the sidebar, showing topic and last message. Click to reopen past conversations.
6. Conversation manager & prompt orchestration (Phase III)
This is the core logic, mainly in main.py (also used by backend.py):
   - System prompt (build_system_prompt):
       Sets the interview tone, allowed topics, and rules like “one question at a time” and “no candidate role-playing.”
   - History formatting (format_messages):
       Turns the conversation into a plain-text chat format:
         - System: &lt;system prompt&gt;
         - Alternating Candidate: and Interviewer: messages
         - Ends with “Ask exactly one short AI/ML question now.”
   - Topic specialization:
        On the first message, if a topic is provided, it adds a clause to focus questions on that topic.
   - Turn-taking:
      - Each user response appends to the history.
      - The model generates the next interviewer question (only up to the first ? to keep it concise).
      - That question is added as the next interviewer message.
This way, the conversation manager keeps things simple and effective — no external tools or retrieval, just smart prompt design and managing conversation history.

7. Managing context memory & latency (Phase II)
   - The backend stores conversation history only per WebSocket connection (no cross-session memory).
   - Each turn rebuilds the prompt from:
       - The fixed system prompt (plus any topic restriction)
       - The full chat history for that session
   - This respects the rule that all intelligence comes from the prompt + context, no external data sources.
If you want to limit memory usage for very long interviews, you can trim the history to the last N turns (e.g., 10 Q&A pairs) before formatting it. The current setup keeps the full history and usually fits well within the N_CTX=4096 token limit.

Latency measurement:
   - The REST /api/chat endpoint returns a latency_seconds value.
   - To benchmark latency, you can use the included postman_collection.json in Postman:
     1. Send multiple POST /api/chat requests with different prompts.
     2. Note reported latency values.
     3. Summarize results in the README under a new heading, including CPU specs, average latency, and tokens per second from llama logs.
8. Backend API & microservices (Phase IV)
The backend architecture looks like this:
flowchart LR
  UI[Web UI<br>HTML/JS] &lt;--&gt; WS[FastAPI<br>WebSocket /ws/chat]
  UI --&gt; REST[FastAPI<br>REST /api/chat]
  WS --&gt; CM[Conversation Manager<br>prompt + history]
  REST --&gt; CM
  CM --&gt; LLM[Local LLM Engine<br>llama-cpp-python + GGUF]
Key endpoints:

GET / — serves the web UI.
GET /api/health — simple health check returning status and whether the model is loaded.
POST /api/chat — non-streaming chat for testing, accepts { "topic": "...", "history": [...], "message": "..." }, replies with { "question": "...", "latency_seconds": ..., "history": [...] }.
WS /ws/chat — main streaming chat endpoint:
Client sends { "message": "&lt;your answer&gt;" } (and "topic" on the first message).
Server streams tokens back as JSON chunks { "delta": "...", "done": false }.
Ends with { "message": "&lt;full question&gt;", "done": true }.
Concurrency & async:

FastAPI with Uvicorn handles WebSocket connections asynchronously.
Each connection keeps its own history and system prompt (depending on topic).
The LLM inference is protected by a global lock to avoid conflicts when multiple users connect — so requests are handled one at a time internally but many users can still connect simultaneously.
Streaming details:

Uses llama_cpp.Llama with streaming enabled.
Sends tokens as soon as they are generated.
Stops generating at the first question mark ? to keep questions short and focused.
9. Frontend (Phase V)
The frontend is a single-page app (frontend/index.html) that looks and feels like ChatGPT:
   - Start by selecting a topic.
   - Then jump into a chat view with:
   - User and AI bubbles with avatars.
   - Dark mode and modern style.
   - Live streaming of interviewer questions.
   - Textarea input with handy Enter and Shift+Enter behavior.
   - A sidebar that keeps your previous sessions saved in localStorage.
   - Click on old sessions to view the full transcript.
   - A “New session” button lets you restart with a new topic and fresh connection.
10. Docker & deployment (Phase IV)
There’s a Dockerfile included so you can run this in a container easily:
  - It’s CPU-only.
  - Installs dependencies from requirements.txt.
  - Expects the GGUF model at /app/models/ECE-Qwen0.5B-FT-V2.Q2_K.gguf (or you can specify a different path with the MODEL_PATH environment variable).
  - Runs the server on port 8000.
  -  To build and run:

docker build -t conversational-ai-system .
docker run -p 8000:8000 -e MODEL_PATH=models/ECE-Qwen0.5B-FT-V2.Q2_K.gguf conversational-ai-system
Open your browser at http://127.0.0.1:8000/ to start.

11. Postman collection (Phase IV)
A postman_collection.json file is provided to help you test the APIs easily:

Includes tests for GET /api/health and POST /api/chat.
Just import it into Postman and update the URL and port if needed.
12. Production readiness & evaluation (Phase VI)
How to test latency & stress:

Run repeated API calls to POST /api/chat (using the provided benchmark script or your own tool).
Watch the latency_seconds output and server logs to see how well it handles load.
You can run the benchmark script like this:

.\.venv\Scripts\python.exe scripts\benchmark_rest.py
How failures are handled:

If the model file is missing, the backend will fail immediately with a clear error.
The WebSocket endpoint handles client disconnects gracefully using try/except on disconnect events.
Known limitations:

CPU-only inference means larger models can be slow.
No external tools or retrieval — everything is done via prompts and context only.
Session history is kept in memory per connection; very long chats might approach token limits (can be fixed by trimming history).
