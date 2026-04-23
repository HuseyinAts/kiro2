"""
Anthropic Claude Provider Implementation
Supports Claude 3.5 Sonnet and other Claude models

Author: KIRO AI Team
Date: 2025-10-19
"""

import asyncio
import json
import time
import uuid
from typing import Any

from anthropic import Anthropic, AsyncAnthropic

from services.llm.base_llm_provider import BaseLLMProvider, LLMRequest, LLMResponse
from services.llm.multi_llm_config import LLMCapability, LLMModelConfig, LLMProvider
from services.llm.turkish_optimizer import TurkishPromptOptimizer


class ClaudeProvider(BaseLLMProvider):
    """
    Anthropic Claude Provider

    Features:
    - Claude 3.5 Sonnet (latest)
    - Fast response times
    - Cost-effective
    - High quality Turkish language understanding
    """

    def __init__(self, config: LLMModelConfig):
        """Initialize Claude provider"""
        super().__init__(config)

        if not self.api_key:
            raise ValueError("Anthropic API key is required")

        # Initialize async and sync clients
        self.async_client = AsyncAnthropic(api_key=self.api_key)
        self.sync_client = Anthropic(api_key=self.api_key)

        # Initialize Turkish prompt optimizer
        self.optimizer = TurkishPromptOptimizer(
            common_words_path="backend/data/turkish_common_words_1000.json"
        )

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate text using Claude API

        Args:
            request: LLM request

        Returns:
            LLM response
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())

        # Turkish prompt optimization
        original_prompt = request.prompt
        original_system_prompt = request.system_prompt

        if request.prompt:
            optimized = self.optimizer.optimize(request.prompt)
            request.prompt = optimized.optimized_prompt

        if request.system_prompt:
            optimized_system = self.optimizer.optimize(request.system_prompt)
            request.system_prompt = optimized_system.optimized_prompt

        try:
            # Prepare API parameters
            # NOTE: Claude API does not support both temperature and top_p
            # Using only temperature for Claude
            api_params = {
                "model": self.model_name,
                "max_tokens": request.max_tokens or self.config.max_tokens,
                "temperature": request.temperature or self.config.temperature,
                # top_p removed - Claude doesn't support both temperature and top_p
                "messages": [{"role": "user", "content": request.prompt}],
            }

            # Add system prompt if provided
            if request.system_prompt:
                api_params["system"] = request.system_prompt

            # Add stop sequences if provided
            if request.stop_sequences:
                api_params["stop_sequences"] = request.stop_sequences

            # Make API call with retry
            response = await self._retry_with_backoff(
                lambda: self.async_client.messages.create(**api_params)
            )

            # Extract response data
            content = response.content[0].text if response.content else ""
            tokens_used = response.usage.input_tokens + response.usage.output_tokens

            # Calculate metrics
            latency_ms = (time.time() - start_time) * 1000
            cost = self._calculate_cost(tokens_used)

            # Update metrics
            self._update_metrics(latency_ms, tokens_used, cost)

            return LLMResponse(
                provider=LLMProvider.CLAUDE,
                model_name=response.model,
                content=content,
                raw_response=response.model_dump(),
                latency_ms=latency_ms,
                tokens_used=tokens_used,
                cost_usd=cost,
                request_id=request_id,
            )

        except Exception as e:
            raise RuntimeError(f"Claude API error: {e!s}")

    async def generate_batch(self, requests: list[LLMRequest]) -> list[LLMResponse]:
        """
        Generate text for multiple requests concurrently

        Args:
            requests: List of LLM requests

        Returns:
            List of LLM responses
        """
        tasks = [self.generate(request) for request in requests]
        return await asyncio.gather(*tasks)

    async def check_health(self) -> bool:
        """
        Check Claude API health

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Simple test request
            test_request = LLMRequest(prompt="Hello", max_tokens=5)
            response = await self.generate(test_request)
            return len(response.content) > 0
        except Exception:
            return False

    def supports_capability(self, capability: LLMCapability) -> bool:
        """Check if capability is supported"""
        return capability in self.config.capabilities

    async def fine_tune(
        self, training_file: str, validation_file: str | None = None, **kwargs
    ) -> str:
        """
        Claude doesn't support fine-tuning via API yet

        Args:
            training_file: Training file path
            validation_file: Validation file path
            **kwargs: Additional parameters

        Returns:
            Model ID (original model)
        """
        # Note: Claude fine-tuning is available through Anthropic's enterprise plan
        # For now, we use prompt engineering and few-shot learning
        print(
            "Claude fine-tuning not available via API. Using base model with prompt engineering."
        )
        return self.model_name

    async def create_osym_question(
        self,
        topic: str,
        subtopic: str,
        difficulty: float,
        bloom_level: int,
        exam_type: str,
    ) -> dict[str, Any]:
        """
        Generate ÖSYM question using Claude

        Args:
            topic: Main topic
            subtopic: Subtopic
            difficulty: Difficulty level (0.0-1.0)
            bloom_level: Bloom taxonomy level (1-6)
            exam_type: Exam type (TYT, AYT, YDT)

        Returns:
            Generated question as dictionary
        """
        from services.llm.multi_llm_config import MultiLLMConfig

        # Get prompt template
        prompt_template = MultiLLMConfig.TURKISH_OSYM_PROMPTS[
            "question_generation_prompt"
        ]
        system_prompt = MultiLLMConfig.TURKISH_OSYM_PROMPTS["system_prompt"]

        # Format prompt
        prompt = prompt_template.format(
            topic=topic,
            subtopic=subtopic,
            difficulty=difficulty,
            bloom_level=bloom_level,
            exam_type=exam_type,
        )

        # Add JSON formatting instruction
        prompt += "\n\nCevabını sadece JSON formatında ver. Başka hiçbir şey yazma."

        # Generate question
        request = LLMRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.8,  # Higher temperature for creativity
        )

        response = await self.generate(request)

        # Parse JSON response
        try:
            # Extract JSON from response (Claude may add extra text)
            content = response.content.strip()

            # Find JSON object
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                question_data = json.loads(json_str)
                return question_data
            raise ValueError("No JSON object found in response")

        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(
                f"Failed to parse JSON response: {response.content}\nError: {e!s}"
            )

    async def generate_distractors(
        self, question_stem: str, correct_answer: str, topic: str
    ) -> dict[str, Any]:
        """
        Generate distractors for ÖSYM question

        Args:
            question_stem: Question text
            correct_answer: Correct answer text
            topic: Question topic

        Returns:
            Distractors with reasoning
        """
        from services.llm.multi_llm_config import MultiLLMConfig

        prompt_template = MultiLLMConfig.TURKISH_OSYM_PROMPTS[
            "distractor_generation_prompt"
        ]
        system_prompt = MultiLLMConfig.TURKISH_OSYM_PROMPTS["system_prompt"]

        prompt = prompt_template.format(
            question_stem=question_stem, correct_answer=correct_answer, topic=topic
        )

        prompt += "\n\nCevabını sadece JSON formatında ver."

        request = LLMRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.9,  # High creativity for diverse distractors
        )

        response = await self.generate(request)

        try:
            content = response.content.strip()
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                distractors_data = json.loads(json_str)
                return distractors_data
            raise ValueError("No JSON object found in response")

        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(
                f"Failed to parse JSON response: {response.content}\nError: {e!s}"
            )

    async def score_question_quality(
        self, question_stem: str, options: list[str], correct_answer: int
    ) -> dict[str, Any]:
        """
        Score ÖSYM question quality

        Args:
            question_stem: Question text
            options: Answer options
            correct_answer: Index of correct answer

        Returns:
            Quality scores and feedback
        """
        from services.llm.multi_llm_config import MultiLLMConfig

        prompt_template = MultiLLMConfig.TURKISH_OSYM_PROMPTS["quality_scoring_prompt"]
        system_prompt = MultiLLMConfig.TURKISH_OSYM_PROMPTS["system_prompt"]

        prompt = prompt_template.format(
            question_stem=question_stem,
            options=json.dumps(options, ensure_ascii=False),
            correct_answer=options[correct_answer],
        )

        prompt += "\n\nCevabını sadece JSON formatında ver."

        request = LLMRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,  # Low temperature for consistent scoring
        )

        response = await self.generate(request)

        try:
            content = response.content.strip()
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                quality_data = json.loads(json_str)
                return quality_data
            raise ValueError("No JSON object found in response")

        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(
                f"Failed to parse JSON response: {response.content}\nError: {e!s}"
            )
