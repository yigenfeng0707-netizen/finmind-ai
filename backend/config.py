import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/finmind.db")

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Application
APP_NAME = os.getenv("APP_NAME", "FinMind AI")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY", "") or os.urandom(32).hex()

# Data Sources
YAHOO_FINANCE_ENABLED = True
NEWS_API_ENABLED = bool(NEWSAPI_KEY)

# Agent Configuration
MAX_CONCURRENT_AGENTS = 4
AGENT_TIMEOUT = 30  # seconds
ANALYSIS_CACHE_TTL = 300  # 5 minutes

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # openai or anthropic
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2000"))
LLM_ENABLED = os.getenv("LLM_ENABLED", "true").lower() == "true"
