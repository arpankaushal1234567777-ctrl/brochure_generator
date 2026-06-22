# ── Crawling ──────────────────────────────────────────────────────────────────
TOP_N               = 6       # Reduced from 8 — fewer pages, faster crawl
MAX_WORKERS         = 6       # Parallel fetch workers
MAX_CONTENT_WORDS   = 1500    # Reduced: less text → faster summarization
MIN_CONTENT_WORDS   = 80      # Minimum words to consider a page useful

# ── Deduplication ─────────────────────────────────────────────────────────────
SIMILARITY_THRESHOLD = 0.65   # Slightly tighter — drop near-duplicates earlier

# ── LLM ───────────────────────────────────────────────────────────────────────
# Groq model for final section generation
GROQ_MODEL          = "llama-3.1-8b-instant"
GROQ_TEMPERATURE    = 0.1     # Low temp = less hallucination for extraction tasks
GROQ_MAX_TOKENS     = 512     # Brochure sections don't need long output

# Gemini model used for per-page compression
GEMINI_MODEL        = "gemini-2.0-flash"   # Faster than 2.5-flash

# ── Pipeline ──────────────────────────────────────────────────────────────────
COMBINE_TOP_PAGES   = 2       # Use top-2 pages per section (was 1, same cost)
MAX_CHUNK_WORDS     = 1500    # Chunk size fed to Gemini
GEMINI_TIMEOUT_SEC  = 12      # Hard timeout per Gemini call