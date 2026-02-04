"""
Alibaba Qwen Provider Implementation
Supports Qwen 2.5 models (cloud API and local deployment)

Author: KIRO AI Team
Date: 2025-10-19
"""

from typing import Optional, Dict, Any, List
import time
import uuid
import json
import asyncio
import httpx
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

from services.llm.base_llm_provider import BaseLLMProvider, LLMRequest, LLMResponse
from services.llm.multi_llm_config import LLMProvider, LLMModelConfig, LLMCapability


class QwenProvider(BaseLLMProvider):
    """
    Alibaba Qwen Provider

    Features:
    - Qwen 2.5 72B Instruct model
    - Cloud API support (DashScope)
    - Local deployment support (HuggingFace)
    - Fine-tuning with LoRA
    - Turkish language support
    - Free if self-hosted
    """

    def __init__(self, config: LLMModelConfig, use_local: bool = False):
        """
        Initialize Qwen provider

        Args:
            config: LLM model configuration
            use_local: Use local deployment instead of cloud API
        """
        super().__init__(config)

        self.use_local = use_local

        if self.use_local:
            self._init_local_model()
        else:
            if not self.api_key:
                raise ValueError("Qwen API key is required for cloud deployment")
            self._init_cloud_api()

    def _init_local_model(self):
        """Initialize local Qwen model using HuggingFace"""
        print(f"Loading Qwen model locally: {self.model_name}")

        # Check GPU availability
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")

        # Load tokenizer and model
        # Note: For 72B model, you need significant GPU memory (>100GB)
        # Consider using smaller models (7B, 14B) or quantization for local deployment
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name, trust_remote_code=True
            )

            # For local deployment, use smaller model or quantization
            model_name_local = "Qwen/Qwen2.5-7B-Instruct"  # Smaller model for local
            print(f"Using smaller model for local deployment: {model_name_local}")

            self.model = AutoModelForCausalLM.from_pretrained(
                model_name_local,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
                trust_remote_code=True,
            )

            if self.device == "cpu":
                self.model = self.model.to(self.device)

            print("Qwen model loaded successfully")

        except Exception as e:
            raise RuntimeError(f"Failed to load Qwen model: {str(e)}")

    def _init_cloud_api(self):
        """Initialize cloud API client (DashScope/Alibaba Cloud)"""
        self.api_base = self.api_base or "https://dashscope.aliyuncs.com/api/v1"
        self.http_client = httpx.AsyncClient(timeout=60.0)

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate text using Qwen

        Args:
            request: LLM request

        Returns:
            LLM response
        """
        if self.use_local:
            return await self._generate_local(request)
        else:
            return await self._generate_cloud(request)

    async def _generate_local(self, request: LLMRequest) -> LLMResponse:
        """Generate text using local Qwen model"""
        start_time = time.time()
        request_id = str(uuid.uuid4())

        try:
            # Prepare messages
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})

            # Apply chat template
            text = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )

            # Tokenize
            model_inputs = self.tokenizer([text], return_tensors="pt").to(self.device)

            # Generate
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **model_inputs,
                    max_new_tokens=request.max_tokens or self.config.max_tokens,
                    temperature=request.temperature or self.config.temperature,
                    top_p=request.top_p or self.config.top_p,
                    do_sample=True,
                )

            # Decode
            generated_ids = [
                output_ids[len(input_ids) :]
                for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
            ]

            content = self.tokenizer.batch_decode(
                generated_ids, skip_special_tokens=True
            )[0]

            # Calculate metrics
            tokens_used = len(generated_ids[0])
            latency_ms = (time.time() - start_time) * 1000
            cost = 0.0  # Free for local deployment

            # Update metrics
            self._update_metrics(latency_ms, tokens_used, cost)

            return LLMResponse(
                provider=LLMProvider.QWEN,
                model_name=self.model_name,
                content=content,
                latency_ms=latency_ms,
                tokens_used=tokens_used,
                cost_usd=cost,
                request_id=request_id,
            )

        except Exception as e:
            raise RuntimeError(f"Qwen local generation error: {str(e)}")

    async def _generate_cloud(self, request: LLMRequest) -> LLMResponse:
        """Generate text using Qwen cloud API (DashScope)"""
        start_time = time.time()
        request_id = str(uuid.uuid4())

        try:
            # Prepare API request
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})

            api_params = {
                "model": self.model_name,
                "input": {"messages": messages},
                "parameters": {
                    "max_tokens": request.max_tokens or self.config.max_tokens,
                    "temperature": request.temperature or self.config.temperature,
                    "top_p": request.top_p or self.config.top_p,
                },
            }

            # Make API call
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            response = await self.http_client.post(
                f"{self.api_base}/services/aigc/text-generation/generation",
                json=api_params,
                headers=headers,
            )

            response.raise_for_status()
            response_data = response.json()

            # Extract response
            if response_data.get("output"):
                content = response_data["output"]["text"]
                tokens_used = response_data["usage"]["total_tokens"]
            else:
                raise RuntimeError(f"Unexpected API response: {response_data}")

            # Calculate metrics
            latency_ms = (time.time() - start_time) * 1000
            cost = self._calculate_cost(tokens_used)

            # Update metrics
            self._update_metrics(latency_ms, tokens_used, cost)

            return LLMResponse(
                provider=LLMProvider.QWEN,
                model_name=self.model_name,
                content=content,
                raw_response=response_data,
                latency_ms=latency_ms,
                tokens_used=tokens_used,
                cost_usd=cost,
                request_id=request_id,
            )

        except Exception as e:
            raise RuntimeError(f"Qwen cloud API error: {str(e)}")

    async def generate_batch(self, requests: List[LLMRequest]) -> List[LLMResponse]:
        """Generate text for multiple requests"""
        tasks = [self.generate(request) for request in requests]
        return await asyncio.gather(*tasks)

    async def check_health(self) -> bool:
        """Check Qwen API/model health"""
        try:
            test_request = LLMRequest(prompt="Hello", max_tokens=5)
            response = await self.generate(test_request)
            return len(response.content) > 0
        except Exception:
            return False

    def supports_capability(self, capability: LLMCapability) -> bool:
        """Check if capability is supported"""
        return capability in self.config.capabilities

    async def fine_tune(
        self, training_file: str, validation_file: Optional[str] = None, **kwargs
    ) -> str:
        """
        Fine-tune Qwen model using LoRA

        Args:
            training_file: Path to training JSONL file
            validation_file: Path to validation JSONL file
            **kwargs: LoRA parameters

        Returns:
            Fine-tuned model ID/path
        """
        if not self.use_local:
            raise NotImplementedError(
                "Cloud fine-tuning not implemented. Use local deployment."
            )

        try:
            from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
            from transformers import Trainer, TrainingArguments
            import pandas as pd

            # Load training data
            train_data = pd.read_json(training_file, lines=True)

            # LoRA configuration
            lora_config = LoraConfig(
                r=kwargs.get("lora_r", 8),
                lora_alpha=kwargs.get("lora_alpha", 32),
                target_modules=["q_proj", "v_proj"],
                lora_dropout=kwargs.get("lora_dropout", 0.05),
                bias="none",
                task_type="CAUSAL_LM",
            )

            # Prepare model for training
            model = prepare_model_for_kbit_training(self.model)
            model = get_peft_model(model, lora_config)

            # Training arguments
            training_args = TrainingArguments(
                output_dir="./qwen_finetuned",
                num_train_epochs=kwargs.get("n_epochs", 3),
                per_device_train_batch_size=kwargs.get("batch_size", 4),
                learning_rate=kwargs.get("learning_rate", 2e-5),
                save_steps=kwargs.get("save_steps", 100),
                logging_steps=10,
                fp16=True if self.device == "cuda" else False,
            )

            # Prepare dataset for training
            print("Starting fine-tuning...")
            print(f"Training samples: {len(train_data)}")

            # Convert data to Hugging Face dataset format
            from datasets import Dataset

            # Prepare text data for causal language modeling
            def prepare_training_data(examples):
                """Prepare data for training"""
                texts = []
                for item in examples:
                    if isinstance(item, dict):
                        # Format: instruction + input + output
                        instruction = item.get("instruction", "")
                        input_text = item.get("input", "")
                        output = item.get("output", "")

                        if instruction and output:
                            text = f"### İnstrüksiyon:\n{instruction}\n\n"
                            if input_text:
                                text += f"### Girdi:\n{input_text}\n\n"
                            text += f"### Çıktı:\n{output}"
                            texts.append(text)
                return texts

            training_texts = prepare_training_data(train_data.to_dict("records"))

            # Create dataset
            dataset = Dataset.from_dict({"text": training_texts})

            # Tokenize dataset
            def tokenize_function(examples):
                return self.tokenizer(
                    examples["text"],
                    padding="max_length",
                    truncation=True,
                    max_length=kwargs.get("max_length", 512),
                )

            tokenized_dataset = dataset.map(
                tokenize_function, batched=True, remove_columns=dataset.column_names
            )

            # Create data collator
            from transformers import DataCollatorForLanguageModeling

            data_collator = DataCollatorForLanguageModeling(
                tokenizer=self.tokenizer, mlm=False  # Causal LM, not masked LM
            )

            # Create trainer
            from transformers import Trainer

            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=tokenized_dataset,
                data_collator=data_collator,
            )

            # Train model
            print("Training in progress...")
            trainer.train()

            # Save fine-tuned model
            fine_tuned_path = "./qwen_finetuned/final"
            model.save_pretrained(fine_tuned_path)
            self.tokenizer.save_pretrained(fine_tuned_path)

            print(f"Fine-tuning completed. Model saved to: {fine_tuned_path}")

            return fine_tuned_path

        except Exception as e:
            raise RuntimeError(f"Qwen fine-tuning error: {str(e)}")

    async def create_osym_question(
        self,
        topic: str,
        subtopic: str,
        difficulty: float,
        bloom_level: int,
        exam_type: str,
    ) -> Dict[str, Any]:
        """Generate ÖSYM question using Qwen"""
        from services.llm.multi_llm_config import MultiLLMConfig

        prompt_template = MultiLLMConfig.TURKISH_OSYM_PROMPTS[
            "question_generation_prompt"
        ]
        system_prompt = MultiLLMConfig.TURKISH_OSYM_PROMPTS["system_prompt"]

        prompt = prompt_template.format(
            topic=topic,
            subtopic=subtopic,
            difficulty=difficulty,
            bloom_level=bloom_level,
            exam_type=exam_type,
        )

        request = LLMRequest(
            prompt=prompt, system_prompt=system_prompt, temperature=0.8
        )

        response = await self.generate(request)

        try:
            content = response.content.strip()
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                question_data = json.loads(json_str)
                return question_data
            else:
                raise ValueError("No JSON object found in response")

        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(
                f"Failed to parse JSON response: {response.content}\nError: {str(e)}"
            )

    def __del__(self):
        """Cleanup resources"""
        if not self.use_local and hasattr(self, "http_client"):
            asyncio.create_task(self.http_client.aclose())
