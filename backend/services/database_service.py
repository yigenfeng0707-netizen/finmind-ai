import sqlite3
import json
import logging
import os
import tempfile
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Use /tmp on Vercel (writable), fallback to project dir locally
def _get_db_path():
    """Determine the best database path for the current environment."""
    # Vercel sets VERCEL=1
    if os.getenv("VERCEL") == "1":
        return os.path.join(tempfile.gettempdir(), "finmind.db")
    # Local development
    return str(Path(__file__).resolve().parent.parent.parent / "finmind.db")

DB_PATH = _get_db_path()


class DatabaseService:
    """Service for SQLite database operations. Gracefully handles serverless environments."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        self._initialized = False
        self._init_error = None
        # Try to initialize, but don't crash if it fails
        try:
            self._init_db()
            self._initialized = True
        except Exception as e:
            self._init_error = str(e)
            logger.warning(f"Database initialization failed (non-fatal): {e}")

    def _ensure_init(self) -> bool:
        """Ensure database is initialized. Returns True if available."""
        if self._initialized:
            return True
        # Retry once (e.g., /tmp might become available)
        try:
            self._init_db()
            self._initialized = True
            return True
        except Exception as e:
            logger.warning(f"Database still unavailable: {e}")
            return False

    def _init_db(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                company_name TEXT,
                analysis_type TEXT DEFAULT 'comprehensive',
                current_price REAL,
                change_percent REAL,
                recommendation_signal TEXT,
                recommendation_confidence REAL,
                target_price REAL,
                stop_loss REAL,
                reasoning TEXT,
                agent_results TEXT,
                processing_time REAL,
                llm_enhanced INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL UNIQUE,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_analysis_symbol
            ON analysis_history(symbol)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_analysis_created
            ON analysis_history(created_at)
        """)

        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")

    def save_analysis(self, result: Dict[str, Any]) -> int:
        """Save analysis result to database."""
        if not self._ensure_init():
            return -1
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            recommendation = result.get("recommendation", {})
            agent_results = result.get("agent_results", {})

            llm_enhanced = any(
                ar.get("llm_enhanced", False)
                for ar in agent_results.values()
                if isinstance(ar, dict)
            )

            cursor.execute("""
                INSERT INTO analysis_history (
                    symbol, company_name, analysis_type, current_price,
                    change_percent, recommendation_signal, recommendation_confidence,
                    target_price, stop_loss, reasoning, agent_results,
                    processing_time, llm_enhanced
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.get("symbol", ""),
                result.get("company_name", ""),
                result.get("analysis_type", "comprehensive"),
                result.get("current_price"),
                result.get("change_percent"),
                recommendation.get("signal", ""),
                recommendation.get("confidence"),
                recommendation.get("target_price"),
                recommendation.get("stop_loss"),
                recommendation.get("reasoning", ""),
                json.dumps(agent_results, default=str),
                result.get("processing_time"),
                1 if llm_enhanced else 0
            ))

            row_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return row_id

        except Exception as e:
            logger.error(f"Failed to save analysis: {e}")
            return -1

    def get_analysis_history(
        self, symbol: str = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get analysis history, optionally filtered by symbol."""
        if not self._ensure_init():
            return []
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if symbol:
                cursor.execute("""
                    SELECT * FROM analysis_history
                    WHERE symbol = ?
                    ORDER BY created_at DESC LIMIT ?
                """, (symbol.upper(), limit))
            else:
                cursor.execute("""
                    SELECT * FROM analysis_history
                    ORDER BY created_at DESC LIMIT ?
                """, (limit,))

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get analysis history: {e}")
            return []

    def get_latest_analysis(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get the most recent analysis for a symbol."""
        history = self.get_analysis_history(symbol, limit=1)
        return history[0] if history else None

    def get_analysis_stats(self) -> Dict[str, Any]:
        """Get overall analysis statistics."""
        if not self._ensure_init():
            return {"total_analyses": 0}
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM analysis_history")
            total_analyses = cursor.fetchone()[0]

            cursor.execute("""
                SELECT symbol, COUNT(*) as count
                FROM analysis_history
                GROUP BY symbol
                ORDER BY count DESC LIMIT 10
            """)
            top_symbols = [{"symbol": row[0], "count": row[1]} for row in cursor.fetchall()]

            cursor.execute("""
                SELECT recommendation_signal, COUNT(*) as count
                FROM analysis_history
                WHERE recommendation_signal IS NOT NULL
                GROUP BY recommendation_signal
                ORDER BY count DESC
            """)
            signal_distribution = [{row[0]: row[1]} for row in cursor.fetchall()]

            cursor.execute("""
                SELECT AVG(processing_time) FROM analysis_history
            """)
            avg_processing_time = cursor.fetchone()[0] or 0

            conn.close()

            return {
                "total_analyses": total_analyses,
                "top_symbols": top_symbols,
                "signal_distribution": signal_distribution,
                "avg_processing_time": round(avg_processing_time, 2)
            }

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"total_analyses": 0}

    def add_to_watchlist(self, symbol: str) -> bool:
        """Add a symbol to the watchlist."""
        if not self._ensure_init():
            return False
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO watchlist (symbol) VALUES (?)",
                (symbol.upper(),)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to add to watchlist: {e}")
            return False

    def get_watchlist(self) -> List[str]:
        """Get all watchlist symbols."""
        if not self._ensure_init():
            return []
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT symbol FROM watchlist ORDER BY added_at DESC")
            symbols = [row[0] for row in cursor.fetchall()]
            conn.close()
            return symbols
        except Exception as e:
            logger.error(f"Failed to get watchlist: {e}")
            return []


# Singleton instance
db_service = DatabaseService()
