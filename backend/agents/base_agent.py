from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio
import time
from services.llm_service import llm_service


class BaseAgent(ABC):
    """Base class for all AI agents in the FinMind system."""

    def __init__(self, name: str, agent_type: str):
        self.name = name
        self.agent_type = agent_type
        self.is_running = False
        self.last_execution_time = None
        self.execution_count = 0
        self.error_count = 0

    @abstractmethod
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform analysis on the given data. Must be implemented by subclasses."""
        pass

    async def _llm_analyze(self, system_prompt: str, user_prompt: str, output_schema: dict = None) -> dict:
        """Use LLM for analysis if available, otherwise return None."""
        if not llm_service.is_available():
            return None
        try:
            if output_schema:
                return await llm_service.generate_structured(system_prompt, user_prompt, output_schema)
            else:
                text = await llm_service.generate(system_prompt, user_prompt)
                return {"llm_analysis": text}
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"LLM analysis failed for {self.name}: {e}")
            return None

    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent with timing and error handling."""
        self.is_running = True
        start_time = time.time()

        try:
            result = await self.analyze(data)
            execution_time = time.time() - start_time

            self.last_execution_time = datetime.now()
            self.execution_count += 1

            return {
                "agent_name": self.name,
                "agent_type": self.agent_type,
                "status": "success",
                "execution_time": round(execution_time, 3),
                "timestamp": datetime.now().isoformat(),
                "result": result
            }

        except Exception as e:
            self.error_count += 1
            return {
                "agent_name": self.name,
                "agent_type": self.agent_type,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

        finally:
            self.is_running = False

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "name": self.name,
            "type": self.agent_type,
            "is_running": self.is_running,
            "last_execution": self.last_execution_time,
            "execution_count": self.execution_count,
            "error_count": self.error_count,
            "success_rate": (
                (self.execution_count - self.error_count) / self.execution_count
                if self.execution_count > 0
                else 0
            )
        }
