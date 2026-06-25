APP_TITLE = "StudyBuddy AI"
APP_VERSION = "1.0.0"
APP_ICON = "📚"

SUPPORTED_FORMATS = ["pdf", "docx", "txt", "pptx"]
SUPPORTED_FORMATS_DISPLAY = ["PDF", "DOCX", "TXT", "PPTX"]
MAX_FILE_SIZE_MB = 50
MAX_TEXT_LENGTH = 15000  # chars sent to Gemini

GEMINI_MODEL = "gemini-2.5-flash"

COLORS = {
    "bg_primary": "#F8F4E8",
    "bg_card": "#FFFFFF",
    "accent": "#0F2D52",
    "accent_hover": "#163C6D",
    "text_primary": "#1F2937",
    "text_secondary": "#6B7280",
    "border": "#E5E7EB",
    "success": "#2F6B4F",
    "error": "#8A4F46",
    "warning": "#9B6C2D",
}

NAV_ITEMS = [
    {"title": "Home", "icon": "🏠", "page": "pages/1_Home.py"},
    {"title": "Explanation", "icon": "📖", "page": "pages/2_Explanation.py"},
    {"title": "Summary", "icon": "📝", "page": "pages/3_Summary.py"},
    {"title": "Quiz", "icon": "🧠", "page": "pages/4_Quiz.py"},
    {"title": "Flashcards", "icon": "🃏", "page": "pages/5_Flashcards.py"},
    {"title": "History", "icon": "📚", "page": "pages/6_History.py"},
]
