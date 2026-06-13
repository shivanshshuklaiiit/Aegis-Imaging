from abc import ABC, abstractmethod
import time


class BaseAgent(ABC):
    name: str = "base"

    async def execute(self, context: dict) -> dict:
        start = time.time()
        try:
            result = await self.run(context)
            result["agent"] = self.name
            result["latency_ms"] = int((time.time() - start) * 1000)
            result["error"] = None
        except Exception as e:
            result = {
                "agent": self.name,
                "score": 0.0,
                "evidence": [],
                "latency_ms": int((time.time() - start) * 1000),
                "error": str(e),
            }
        return result

    @abstractmethod
    async def run(self, context: dict) -> dict:
        """
        Args:
          context: shared dict with at minimum:
                   image_path (str), sha256 (str), modality (str)
                   Plus outputs from prior agents keyed by agent name.
        Returns:
          dict with at minimum:
          { score: float, evidence: list, ...domain-specific keys }
          The execute() wrapper adds: agent, latency_ms, error.
        """
        ...
