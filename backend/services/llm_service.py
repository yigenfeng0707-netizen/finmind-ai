import asyncio
import json
import logging
from typing import Optional

from config import OPENAI_API_KEY, ANTHROPIC_API_KEY, SENSENOVA_API_KEY, SENSENOVA_BASE_URL, SENSENOVA_MODEL

logger = logging.getLogger(__name__)


class LLMService:
    """Unified LLM service supporting OpenAI, Anthropic, and SenseNova APIs with graceful fallback."""

    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        self.sensenova_client = None
        self.provider: Optional[str] = None
        self.available: bool = False
        self.default_model: Optional[str] = None

        # Try SenseNova first (OpenAI-compatible, free/cheap for hackathon)
        if SENSENOVA_API_KEY:
            try:
                from openai import AsyncOpenAI

                self.sensenova_client = AsyncOpenAI(
                    api_key=SENSENOVA_API_KEY,
                    base_url=SENSENOVA_BASE_URL,
                )
                self.provider = "sensenova"
                self.default_model = SENSENOVA_MODEL
                self.available = True
                logger.info("LLM provider initialized: SenseNova (%s)", SENSENOVA_MODEL)
            except Exception as e:
                logger.warning("Failed to initialize SenseNova client: %s", e)

        # Try OpenAI
        if not self.available and OPENAI_API_KEY:
            try:
                from openai import AsyncOpenAI

                self.openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
                self.provider = "openai"
                self.default_model = "gpt-4o-mini"
                self.available = True
                logger.info("LLM provider initialized: OpenAI")
            except Exception as e:
                logger.warning("Failed to initialize OpenAI client: %s", e)

        # Fallback to Anthropic
        if not self.available and ANTHROPIC_API_KEY:
            try:
                from anthropic import AsyncAnthropic

                self.anthropic_client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
                self.provider = "anthropic"
                self.default_model = "claude-sonnet-4-20250514"
                self.available = True
                logger.info("LLM provider initialized: Anthropic")
            except Exception as e:
                logger.warning("Failed to initialize Anthropic client: %s", e)

        if not self.available:
            logger.warning(
                "No LLM provider available. Set SENSENOVA_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY."
            )

    def is_available(self) -> bool:
        """Check if any LLM provider is configured."""
        return self.available

    async def _retry_request(
        self,
        func,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 10.0,
    ):
        """Execute an async function with exponential backoff retry."""
        last_exception = None
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(
                        "LLM request failed (attempt %d/%d), retrying in %.1fs: %s",
                        attempt + 1, max_retries, delay, e
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        "LLM request failed after %d attempts: %s",
                        max_retries, e
                    )
        raise last_exception

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> str:
        """Generate text completion using the configured LLM provider."""
        if not self.available:
            logger.error("No LLM provider available for generation.")
            return ""

        try:
            if self.provider == "sensenova":
                return await self._retry_request(
                    lambda: self._generate_sensenova(
                        system_prompt, user_prompt, model, temperature, max_tokens
                    )
                )
            elif self.provider == "openai":
                return await self._retry_request(
                    lambda: self._generate_openai(
                        system_prompt, user_prompt, model, temperature, max_tokens
                    )
                )
            elif self.provider == "anthropic":
                return await self._retry_request(
                    lambda: self._generate_anthropic(
                        system_prompt, user_prompt, model, temperature, max_tokens
                    )
                )
        except Exception as e:
            logger.error("LLM generation failed with %s after retries: %s", self.provider, e)
            # Try fallback provider
            fallback_result = await self._try_fallback(
                system_prompt, user_prompt, model, temperature, max_tokens
            )
            if fallback_result is not None:
                return fallback_result

        return ""

    async def _generate_sensenova(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Generate using SenseNova (OpenAI-compatible API)."""
        model = model or self.default_model or "sensenova-6.7-flash-lite"
        response = await self.sensenova_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if response.choices and len(response.choices) > 0 and response.choices[0].message:
            return response.choices[0].message.content or ""
        return ""

    async def _generate_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        model = model or "gpt-4o-mini"
        response = await self.openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    async def _generate_anthropic(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        model = model or "claude-sonnet-4-20250514"
        response = await self.anthropic_client.messages.create(
            model=model,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if response.content and len(response.content) > 0:
            return response.content[0].text if hasattr(response.content[0], 'text') else str(response.content[0])
        return ""

    async def _try_fallback(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> Optional[str]:
        """Attempt generation with a fallback provider."""
        # Try SenseNova first as fallback (cheapest)
        if self.provider != "sensenova" and self.sensenova_client:
            try:
                logger.info("Falling back to SenseNova provider.")
                return await self._generate_sensenova(
                    system_prompt, user_prompt, model, temperature, max_tokens
                )
            except Exception as e:
                logger.error("SenseNova fallback failed: %s", e)

        # Try OpenAI as fallback
        if self.provider != "openai" and self.openai_client:
            try:
                logger.info("Falling back to OpenAI provider.")
                return await self._generate_openai(
                    system_prompt, user_prompt, model, temperature, max_tokens
                )
            except Exception as e:
                logger.error("OpenAI fallback failed: %s", e)

        # Try Anthropic as fallback
        if self.provider != "anthropic" and self.anthropic_client:
            try:
                logger.info("Falling back to Anthropic provider.")
                return await self._generate_anthropic(
                    system_prompt, user_prompt, model, temperature, max_tokens
                )
            except Exception as e:
                logger.error("Anthropic fallback failed: %s", e)

        return None

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: dict,
        model: str = None,
    ) -> dict:
        """Generate structured JSON output matching the provided schema."""
        if not self.available:
            logger.error("No LLM provider available for structured generation.")
            return self._default_structure(output_schema)

        schema_str = json.dumps(output_schema, indent=2, ensure_ascii=False)
        structured_instruction = (
            f"{system_prompt}\n\n"
            "You MUST respond with valid JSON that conforms to the following schema. "
            "Do NOT include any text outside the JSON object.\n\n"
            f"Schema:\n{schema_str}"
        )

        try:
            raw = await self.generate(
                system_prompt=structured_instruction,
                user_prompt=user_prompt,
                model=model,
                temperature=0.2,
                max_tokens=2000,
            )

            # Strip markdown code fences if present
            text = raw.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                # Remove first line (```json or ```) and last line (```)
                lines = [l for l in lines if not l.strip().startswith("```")]
                text = "\n".join(lines).strip()

            result = json.loads(text)
            return result

        except json.JSONDecodeError as e:
            logger.error("Failed to parse structured LLM output as JSON: %s", e)
            logger.debug("Raw LLM output was: %s", raw[:500] if 'raw' in dir() else 'N/A')
            return self._default_structure(output_schema)
        except Exception as e:
            logger.error("Structured generation failed: %s", e)
            return self._default_structure(output_schema)

    @staticmethod
    def _default_structure(schema: dict) -> dict:
        """Build a default/empty structure from a JSON schema."""
        result = {}
        properties = schema.get("properties", {})
        for key, prop in properties.items():
            prop_type = prop.get("type", "string")
            if prop_type == "string":
                result[key] = prop.get("default", "")
            elif prop_type == "number":
                result[key] = prop.get("default", 0.0)
            elif prop_type == "integer":
                result[key] = prop.get("default", 0)
            elif prop_type == "boolean":
                result[key] = prop.get("default", False)
            elif prop_type == "array":
                result[key] = prop.get("default", [])
            elif prop_type == "object":
                result[key] = prop.get("default", {})
            else:
                result[key] = None
        return result

    @staticmethod
    def validate_agent_result(result: dict) -> dict:
        """Validate and sanitize LLM agent output, falling back to safe defaults."""
        valid_signals = {"strong_buy", "buy", "hold", "sell", "strong_sell"}

        # Validate signal
        if "signal" in result:
            signal = result["signal"]
            if signal not in valid_signals:
                # Try to map common variations
                signal_map = {
                    "strong buy": "strong_buy", "STRONG_BUY": "strong_buy",
                    "buy": "buy", "BUY": "buy",
                    "hold": "hold", "HOLD": "hold", "neutral": "hold",
                    "sell": "sell", "SELL": "sell",
                    "strong sell": "strong_sell", "STRONG_SELL": "strong_sell",
                }
                result["signal"] = signal_map.get(signal, "hold")

        # Validate confidence (must be 0-1)
        if "confidence" in result:
            try:
                conf = float(result["confidence"])
                if conf < 0:
                    conf = 0
                elif conf > 1:
                    conf = 1
                result["confidence"] = round(conf, 2)
            except (ValueError, TypeError):
                result["confidence"] = 0.5

        # Ensure key_findings and risk_factors are string lists
        for key in ["key_findings", "risk_factors", "risk_warnings"]:
            if key in result:
                if not isinstance(result[key], list):
                    result[key] = []
                else:
                    result[key] = [str(f) for f in result[key] if f is not None]

        return result

    @staticmethod
    def _build_financial_context(data: dict) -> str:
        """Format financial data into a context string for LLM prompts."""
        if not data:
            return "No financial data available."

        parts = []

        # Price information
        if "price" in data or "current_price" in data:
            price = data.get("current_price", data.get("price"))
            parts.append(f"Current Price: {price}")

        if "change" in data:
            parts.append(f"Price Change: {data['change']}")

        if "change_percent" in data:
            parts.append(f"Change %: {data['change_percent']}")

        # Volume
        if "volume" in data:
            parts.append(f"Volume: {data['volume']}")

        # Market cap
        if "market_cap" in data:
            parts.append(f"Market Cap: {data['market_cap']}")

        # Technical indicators
        if "rsi" in data:
            parts.append(f"RSI: {data['rsi']}")

        if "macd" in data:
            parts.append(f"MACD: {data['macd']}")

        if "sma_20" in data:
            parts.append(f"SMA 20: {data['sma_20']}")

        if "sma_50" in data:
            parts.append(f"SMA 50: {data['sma_50']}")

        if "bollinger_upper" in data or "bollinger_lower" in data:
            upper = data.get("bollinger_upper", "N/A")
            lower = data.get("bollinger_lower", "N/A")
            parts.append(f"Bollinger Bands: [{lower}, {upper}]")

        # Sentiment
        if "sentiment_score" in data:
            parts.append(f"Sentiment Score: {data['sentiment_score']}")

        if "sentiment_label" in data:
            parts.append(f"Sentiment Label: {data['sentiment_label']}")

        # News
        if "recent_news" in data:
            news_items = data["recent_news"]
            if isinstance(news_items, list) and news_items:
                news_str = "; ".join(
                    f"{n.get('title', n) if isinstance(n, dict) else n}"
                    for n in news_items[:5]
                )
                parts.append(f"Recent News: {news_str}")

        # Earnings
        if "pe_ratio" in data:
            parts.append(f"P/E Ratio: {data['pe_ratio']}")

        if "eps" in data:
            parts.append(f"EPS: {data['eps']}")

        # Any remaining keys not yet handled
        handled_keys = {
            "price", "current_price", "change", "change_percent",
            "volume", "market_cap", "rsi", "macd", "sma_20", "sma_50",
            "bollinger_upper", "bollinger_lower", "sentiment_score",
            "sentiment_label", "recent_news", "pe_ratio", "eps",
        }
        extra = {k: v for k, v in data.items() if k not in handled_keys}
        if extra:
            for k, v in extra.items():
                parts.append(f"{k.replace('_', ' ').title()}: {v}")

        return "\n".join(parts)


llm_service = LLMService()
