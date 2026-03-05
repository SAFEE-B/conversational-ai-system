// ─── Backend connection config ───────────────────────────────
// For local development, leave these as-is.
// For production (e.g. Render), set these to your backend's URL:
//   API_BASE = 'https://your-backend.onrender.com'
//   WS_BASE  = 'wss://your-backend.onrender.com'

const IS_LOCAL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

const API_BASE = IS_LOCAL
    ? 'http://localhost:8000'
    : 'https://REPLACE_WITH_YOUR_BACKEND_URL.onrender.com';

const WS_BASE = IS_LOCAL
    ? 'ws://localhost:8000'
    : 'wss://REPLACE_WITH_YOUR_BACKEND_URL.onrender.com';
