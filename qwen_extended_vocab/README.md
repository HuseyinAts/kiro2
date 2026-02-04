# Qwen Turkish Vocabulary Extension

## Overview

This directory contains the extended vocabulary and configuration for Qwen 2.5 with Turkish language optimization.

## Files

- `tokenizer_config.json`: Extended tokenizer configuration
- `training_data.jsonl`: Training data for vocabulary adaptation (JSONL format)
- `lora_config.json`: LoRA fine-tuning configuration
- `new_tokens.json`: List of 2330 new Turkish tokens
- `README.md`: This file

## Statistics

- **Base Vocabulary Size**: 151,936
- **Extended Vocabulary Size**: 154,266
- **New Tokens Added**: 2,330
- **Expansion**: 1.53%

## Usage

### 1. Load Extended Tokenizer

```python
from transformers import AutoTokenizer

# Load base tokenizer
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B")

# Add new tokens
import json
with open('new_tokens.json', 'r', encoding='utf-8') as f:
    new_tokens = json.load(f)['tokens']

num_added = tokenizer.add_tokens(new_tokens)
print(f"Added {num_added} tokens")
```

### 2. Fine-tune with LoRA

```python
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM
import json

# Load model
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-7B")

# Resize embeddings for new tokens
model.resize_token_embeddings(len(tokenizer))

# Load LoRA config
with open('lora_config.json', 'r') as f:
    lora_config_dict = json.load(f)

lora_config = LoraConfig(**lora_config_dict)
model = get_peft_model(model, lora_config)

# Train on training_data.jsonl
# ... (training code)
```

### 3. Expected Improvements

- **Token Efficiency**: 30-40% reduction in token count for Turkish text
- **Cost Savings**: 30-40% reduction in API costs
- **Better Turkish Understanding**: Improved morphological awareness
- **OSYM Question Quality**: Better handling of Turkish exam terminology

## Training Recommendations

- **Steps**: 10,000
- **Learning Rate**: 0.0001
- **Batch Size**: 4-8 (depending on GPU)
- **Gradient Accumulation**: 4-8 steps
- **Warmup**: 10% of total steps
- **Training Data**: 4,660 sentences (included)

## Next Steps

1. Fine-tune Qwen model with extended vocabulary
2. Evaluate on Turkish OSYM question generation
3. Compare token efficiency before/after
4. Deploy to production

## License

Same as Qwen 2.5 base model (Apache 2.0)

## Contact

KIRO AI Team - 2025-10-19
