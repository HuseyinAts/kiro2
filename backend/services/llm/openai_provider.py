"""
OpenAI GPT-4 Provider Implementation
Supports GPT-4, GPT-4 Turbo, and fine-tuned models

Author: KIRO AI Team
Date: 2025-10-19
"""

import asyncio
import json
import time
import uuid
from typing import Any

from openai import AsyncOpenAI, OpenAI
from openai.types.chat import ChatCompletion

from monitoring.token_usage_tracker import get_tracker
from services.llm.base_llm_provider import BaseLLMProvider, LLMRequest, LLMResponse
from services.llm.multi_llm_config import LLMCapability, LLMModelConfig, LLMProvider
from services.llm.turkish_optimizer import TurkishPromptOptimizer


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI GPT-4 Provider

    Features:
    - GPT-4 Turbo support
    - Fine-tuning support
    - JSON mode
    - Function calling
    - Batch processing
    """

    def __init__(self, config: LLMModelConfig):
        """Initialize OpenAI provider"""
        super().__init__(config)

        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        # Initialize async and sync clients
        self.async_client = AsyncOpenAI(api_key=self.api_key)
        self.sync_client = OpenAI(api_key=self.api_key)

        # Initialize Turkish prompt optimizer
        self.optimizer = TurkishPromptOptimizer(
            common_words_path="backend/data/turkish_common_words_1000.json"
        )

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate text using OpenAI API

        Args:
            request: LLM request

        Returns:
            LLM response
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())

        # Turkish prompt optimization with tracking
        original_prompt_tokens = 0
        optimized_prompt_tokens = 0

        if request.prompt:
            optimized = self.optimizer.optimize(request.prompt)
            original_prompt_tokens += optimized.original_tokens
            optimized_prompt_tokens += optimized.optimized_tokens
            request.prompt = optimized.optimized_prompt

        if request.system_prompt:
            optimized_system = self.optimizer.optimize(request.system_prompt)
            original_prompt_tokens += optimized_system.original_tokens
            optimized_prompt_tokens += optimized_system.optimized_tokens
            request.system_prompt = optimized_system.optimized_prompt

        try:
            # Prepare messages
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})

            # Prepare API parameters
            api_params = {
                "model": self.config.fine_tuned_model_id or self.model_name,
                "messages": messages,
                "max_tokens": request.max_tokens or self.config.max_tokens,
                "temperature": request.temperature or self.config.temperature,
                "top_p": request.top_p or self.config.top_p,
            }

            # Enable JSON mode if requested
            if request.json_mode:
                api_params["response_format"] = {"type": "json_object"}

            # Add stop sequences if provided
            if request.stop_sequences:
                api_params["stop"] = request.stop_sequences

            # Make API call with retry
            response: ChatCompletion = await self._retry_with_backoff(
                lambda: self.async_client.chat.completions.create(**api_params)
            )

            # Extract response data
            content = response.choices[0].message.content or ""
            tokens_used = response.usage.total_tokens if response.usage else 0

            # Calculate metrics
            latency_ms = (time.time() - start_time) * 1000
            cost = self._calculate_cost(tokens_used)

            # Update metrics
            self._update_metrics(latency_ms, tokens_used, cost)

            # Log token usage optimization
            if original_prompt_tokens > 0:
                tracker = get_tracker()
                tracker.log_usage(
                    provider="openai",
                    request_id=request_id,
                    original_tokens=original_prompt_tokens,
                    optimized_tokens=optimized_prompt_tokens,
                    cost_per_1k=self.config.cost_per_1k_tokens,
                )

            return LLMResponse(
                provider=LLMProvider.OPENAI,
                model_name=response.model,
                content=content,
                raw_response=response.model_dump(),
                latency_ms=latency_ms,
                tokens_used=tokens_used,
                cost_usd=cost,
                request_id=request_id,
            )

        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e!s}")

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
        Check OpenAI API health

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
        Fine-tune GPT-4 model

        Args:
            training_file: Path to training JSONL file
            validation_file: Path to validation JSONL file (optional)
            **kwargs: Additional fine-tuning parameters

        Returns:
            Fine-tuned model ID
        """
        try:
            # Upload training file
            with open(training_file, "rb") as f:
                training_file_obj = self.sync_client.files.create(
                    file=f, purpose="fine-tune"
                )

            # Upload validation file if provided
            validation_file_id = None
            if validation_file:
                with open(validation_file, "rb") as f:
                    validation_file_obj = self.sync_client.files.create(
                        file=f, purpose="fine-tune"
                    )
                    validation_file_id = validation_file_obj.id

            # Create fine-tuning job
            fine_tune_params = {
                "training_file": training_file_obj.id,
                "model": self.model_name,
                **kwargs,
            }

            if validation_file_id:
                fine_tune_params["validation_file"] = validation_file_id

            fine_tune_job = self.sync_client.fine_tuning.jobs.create(**fine_tune_params)

            print(f"Fine-tuning job created: {fine_tune_job.id}")
            print(f"Status: {fine_tune_job.status}")

            # Wait for completion (in production, use webhooks)
            while True:
                job_status = self.sync_client.fine_tuning.jobs.retrieve(
                    fine_tune_job.id
                )
                print(f"Fine-tuning status: {job_status.status}")

                if job_status.status == "succeeded":
                    fine_tuned_model_id = job_status.fine_tuned_model
                    print(f"Fine-tuning completed! Model ID: {fine_tuned_model_id}")

                    # Update config with fine-tuned model
                    self.config.fine_tuned_model_id = fine_tuned_model_id
                    return fine_tuned_model_id

                if job_status.status in ["failed", "cancelled"]:
                    raise RuntimeError(f"Fine-tuning {job_status.status}")

                # Wait before checking again
                await asyncio.sleep(60)

        except Exception as e:
            raise RuntimeError(f"Fine-tuning error: {e!s}")

    async def create_osym_question(
        self,
        topic: str,
        subtopic: str,
        difficulty: float,
        bloom_level: int,
        exam_type: str,
    ) -> dict[str, Any]:
        """
        Generate ÖSYM question using fine-tuned model

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

        # Generate question
        request = LLMRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            json_mode=True,
            temperature=0.8,  # Higher temperature for creativity
        )

        response = await self.generate(request)

        # Parse JSON response
        try:
            question_data = json.loads(response.content)
            return question_data
        except json.JSONDecodeError:
            raise ValueError(f"Failed to parse JSON response: {response.content}")

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

        request = LLMRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            json_mode=True,
            temperature=0.9,  # High creativity for diverse distractors
        )

        response = await self.generate(request)

        try:
            distractors_data = json.loads(response.content)
            return distractors_data
        except json.JSONDecodeError:
            raise ValueError(f"Failed to parse JSON response: {response.content}")

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

        request = LLMRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            json_mode=True,
            temperature=0.3,  # Low temperature for consistent scoring
        )

        response = await self.generate(request)

        try:
            quality_data = json.loads(response.content)
            return quality_data
        except json.JSONDecodeError:
            raise ValueError(f"Failed to parse JSON response: {response.content}")
