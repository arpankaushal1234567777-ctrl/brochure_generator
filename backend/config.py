# Crawling
TOP_N = 8
MAX_WORKERS = 6
MAX_CONTENT_WORDS = 2000
MIN_CONTENT_WORDS = 60

# Deduplication
SIMILARITY_THRESHOLD = 0.80

# LLM
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_TEMPERATURE = 0.0
GROQ_MAX_TOKENS = 2048
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_TIMEOUT_SEC = 8

# Pipeline
COMBINE_TOP_PAGES = 4
MAX_CHUNK_WORDS = 1400
MIN_SECTION_SOURCE_WORDS = 40
MAX_ITEMS_PER_SECTION = 12

# Templates
DEFAULT_TEMPLATE = "corporate"
AVAILABLE_TEMPLATES = {
    "corporate": "Corporate",
    "modern": "Modern",
    "minimal": "Minimal",
    "executive": "Executive",
}