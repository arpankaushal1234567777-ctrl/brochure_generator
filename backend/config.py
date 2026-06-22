# ── Crawling ──────────────────────────────────────────────────────────────────
TOP_N               = 6
MAX_WORKERS         = 6
MAX_CONTENT_WORDS   = 1500
MIN_CONTENT_WORDS   = 80

# ── Deduplication ─────────────────────────────────────────────────────────────
SIMILARITY_THRESHOLD = 0.65

# ── LLM (overview only) ───────────────────────────────────────────────────────
GROQ_MODEL          = "llama-3.1-8b-instant"
GROQ_TEMPERATURE    = 0.1
GROQ_MAX_TOKENS     = 512

# ── Pipeline ──────────────────────────────────────────────────────────────────
COMBINE_TOP_PAGES   = 2
