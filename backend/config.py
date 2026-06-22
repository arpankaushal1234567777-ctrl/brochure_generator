# Crawling
TOP_N = 10
MAX_WORKERS = 6
MAX_CONTENT_WORDS = 1800
MIN_CONTENT_WORDS = 80

# Deduplication
SIMILARITY_THRESHOLD = 0.65

# LLM
GROQ_MODEL = "llama-3.1-8b-instant"
GROQ_TEMPERATURE = 0.0
GROQ_MAX_TOKENS = 512
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_TIMEOUT_SEC = 12

# Pipeline
COMBINE_TOP_PAGES = 4
MAX_CHUNK_WORDS = 1600
MIN_SECTION_SOURCE_WORDS = 60
MAX_ITEMS_PER_SECTION = 12

# Templates
DEFAULT_TEMPLATE = "corporate"
AVAILABLE_TEMPLATES = {
    "corporate": "Corporate",
    "modern": "Modern",
    "minimal": "Minimal",
    "executive": "Executive",
}
