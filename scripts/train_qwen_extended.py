"""
Qwen 2.5 Turkish Vocabulary Extension Fine-Tuning
Fine-tunes Qwen with 2,330 new Turkish tokens using LoRA

Author: KIRO AI Team
Date: 2025-10-19

Requirements:
- transformers>=4.35.0
- peft>=0.7.0
- torch>=2.1.0
- datasets>=2.15.0
- accelerate>=0.25.0

Usage:
    python scripts/train_qwen_extended.py --help
"""

import argparse
import json
import os
import sys
from pathlib import Path

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import load_dataset
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QwenTurkishVocabTrainer:
    """
    Qwen Turkish Vocabulary Extension Trainer

    Fine-tunes Qwen 2.5 with extended Turkish vocabulary using LoRA
    """

    def __init__(
        self,
        base_model: str = "Qwen/Qwen2.5-7B",
        vocab_dir: str = "qwen_extended_vocab",
        output_dir: str = "qwen_extended_model",
        use_8bit: bool = False
    ):
        """
        Initialize trainer

        Args:
            base_model: Base Qwen model name
            vocab_dir: Directory containing extended vocabulary files
            output_dir: Output directory for fine-tuned model
            use_8bit: Use 8-bit quantization (reduces memory)
        """
        self.base_model = base_model
        self.vocab_dir = Path(vocab_dir)
        self.output_dir = Path(output_dir)
        self.use_8bit = use_8bit

        self.tokenizer = None
        self.model = None
        self.lora_config = None

    def load_new_tokens(self) -> list:
        """Load new Turkish tokens"""
        tokens_file = self.vocab_dir / "new_tokens.json"

        logger.info(f"Loading new tokens from {tokens_file}...")

        with open(tokens_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        tokens = data['tokens']
        logger.info(f"Loaded {len(tokens)} new tokens")

        return tokens

    def load_lora_config(self) -> LoraConfig:
        """Load LoRA configuration"""
        config_file = self.vocab_dir / "lora_config.json"

        logger.info(f"Loading LoRA config from {config_file}...")

        with open(config_file, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)

        lora_config = LoraConfig(**config_dict)
        logger.info(f"LoRA config loaded: r={lora_config.r}, alpha={lora_config.lora_alpha}")

        return lora_config

    def setup_model_and_tokenizer(self):
        """Setup model and tokenizer with extended vocabulary"""
        logger.info(f"Loading base model: {self.base_model}...")

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.base_model,
            trust_remote_code=True
        )

        original_vocab_size = len(self.tokenizer)
        logger.info(f"Original vocabulary size: {original_vocab_size:,}")

        # Add new Turkish tokens
        new_tokens = self.load_new_tokens()
        num_added = self.tokenizer.add_tokens(new_tokens)
        logger.info(f"Added {num_added} new tokens")

        new_vocab_size = len(self.tokenizer)
        logger.info(f"New vocabulary size: {new_vocab_size:,}")

        # Load model
        model_kwargs = {
            "trust_remote_code": True,
            "device_map": "auto"
        }

        if self.use_8bit:
            model_kwargs["load_in_8bit"] = True
            logger.info("Using 8-bit quantization")
        else:
            model_kwargs["torch_dtype"] = torch.float16
            logger.info("Using float16")

        self.model = AutoModelForCausalLM.from_pretrained(
            self.base_model,
            **model_kwargs
        )

        # Resize model embeddings
        logger.info("Resizing token embeddings...")
        self.model.resize_token_embeddings(len(self.tokenizer))

        # Prepare for LoRA
        logger.info("Preparing model for LoRA...")
        if self.use_8bit:
            self.model = prepare_model_for_kbit_training(self.model)

        # Apply LoRA
        self.lora_config = self.load_lora_config()
        self.model = get_peft_model(self.model, self.lora_config)

        # Print trainable parameters
        self.model.print_trainable_parameters()

    def load_training_data(self):
        """Load training data"""
        training_file = self.vocab_dir / "training_data.jsonl"

        logger.info(f"Loading training data from {training_file}...")

        dataset = load_dataset('json', data_files=str(training_file))

        # Tokenize function
        def tokenize_function(examples):
            return self.tokenizer(
                examples['text'],
                truncation=True,
                padding='max_length',
                max_length=512
            )

        tokenized_dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=['text']
        )

        logger.info(f"Loaded {len(tokenized_dataset['train'])} training examples")

        return tokenized_dataset['train']

    def train(
        self,
        num_epochs: int = 3,
        batch_size: int = 4,
        gradient_accumulation_steps: int = 4,
        learning_rate: float = 1e-4,
        warmup_steps: int = 100,
        save_steps: int = 100
    ):
        """
        Train model

        Args:
            num_epochs: Number of training epochs
            batch_size: Per-device batch size
            gradient_accumulation_steps: Gradient accumulation steps
            learning_rate: Learning rate
            warmup_steps: Warmup steps
            save_steps: Save checkpoint every N steps
        """
        logger.info("Starting training...")

        # Load data
        train_dataset = self.load_training_data()

        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False
        )

        # Training arguments
        training_args = TrainingArguments(
            output_dir=str(self.output_dir),
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            learning_rate=learning_rate,
            warmup_steps=warmup_steps,
            logging_steps=10,
            save_steps=save_steps,
            save_total_limit=3,
            fp16=not self.use_8bit,
            bf16=False,
            optim="adamw_torch",
            report_to="none",
            remove_unused_columns=False
        )

        # Trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            tokenizer=self.tokenizer,
            data_collator=data_collator
        )

        # Train
        logger.info("Training started...")
        trainer.train()

        # Save final model
        final_output = self.output_dir / "final"
        logger.info(f"Saving final model to {final_output}...")

        trainer.save_model(str(final_output))
        self.tokenizer.save_pretrained(str(final_output))

        logger.info("Training complete!")

        return final_output

    def test_model(self, model_path: str):
        """
        Test fine-tuned model

        Args:
            model_path: Path to fine-tuned model
        """
        logger.info(f"Testing model from {model_path}...")

        # Load model and tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="auto"
        )

        # Test prompts
        test_prompts = [
            "ÖSYM sınavında matematik soruları",
            "Türkçe öğrencilerimizden",
            "Aşağıdaki şıklardan doğru olanı işaretleyiniz"
        ]

        logger.info("\n=== Model Test ===\n")

        for prompt in test_prompts:
            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

            # Generate
            outputs = model.generate(
                **inputs,
                max_new_tokens=50,
                temperature=0.7,
                do_sample=True
            )

            generated = tokenizer.decode(outputs[0], skip_special_tokens=True)

            logger.info(f"Prompt: {prompt}")
            logger.info(f"Generated: {generated}\n")


def main():
    parser = argparse.ArgumentParser(description="Train Qwen with Turkish vocabulary extension")

    parser.add_argument(
        "--base_model",
        type=str,
        default="Qwen/Qwen2.5-7B",
        help="Base Qwen model name"
    )
    parser.add_argument(
        "--vocab_dir",
        type=str,
        default="qwen_extended_vocab",
        help="Directory containing extended vocabulary files"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="qwen_extended_model",
        help="Output directory for fine-tuned model"
    )
    parser.add_argument(
        "--num_epochs",
        type=int,
        default=3,
        help="Number of training epochs"
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=4,
        help="Per-device batch size"
    )
    parser.add_argument(
        "--gradient_accumulation_steps",
        type=int,
        default=4,
        help="Gradient accumulation steps"
    )
    parser.add_argument(
        "--learning_rate",
        type=float,
        default=1e-4,
        help="Learning rate"
    )
    parser.add_argument(
        "--use_8bit",
        action="store_true",
        help="Use 8-bit quantization"
    )
    parser.add_argument(
        "--test_only",
        action="store_true",
        help="Only test existing model"
    )

    args = parser.parse_args()

    # Check GPU availability
    if not torch.cuda.is_available():
        logger.warning("No GPU detected! Training will be very slow.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)

    # Create trainer
    trainer = QwenTurkishVocabTrainer(
        base_model=args.base_model,
        vocab_dir=args.vocab_dir,
        output_dir=args.output_dir,
        use_8bit=args.use_8bit
    )

    if args.test_only:
        # Test only
        model_path = Path(args.output_dir) / "final"
        if not model_path.exists():
            logger.error(f"Model not found at {model_path}")
            sys.exit(1)

        trainer.tokenizer = AutoTokenizer.from_pretrained(str(model_path))
        trainer.test_model(str(model_path))
    else:
        # Full training
        trainer.setup_model_and_tokenizer()

        model_path = trainer.train(
            num_epochs=args.num_epochs,
            batch_size=args.batch_size,
            gradient_accumulation_steps=args.gradient_accumulation_steps,
            learning_rate=args.learning_rate
        )

        # Test
        trainer.test_model(str(model_path))

        logger.info("\n=== Training Complete ===")
        logger.info(f"Model saved to: {model_path}")
        logger.info("\nNext steps:")
        logger.info("1. Integrate model with Qwen provider")
        logger.info("2. Run A/B testing")
        logger.info("3. Measure token efficiency improvements")


if __name__ == "__main__":
    main()
