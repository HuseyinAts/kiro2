# BERTurk Education Domain Fine-tuning Pipeline
# Target: Education-specific Turkish NLP

from transformers import (
    AutoTokenizer, AutoModelForSequenceClassification,
    TrainingArguments, Trainer, DataCollatorWithPadding
)
from datasets import Dataset
import torch
from typing import List, Dict, Optional
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support


class BERTurkEducationFineTuner:
    def __init__(
        self,
        base_model: str = "dbmdz/bert-base-turkish-cased",
        num_labels: int = 5,
        device: str = None
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(base_model)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            base_model,
            num_labels=num_labels
        ).to(self.device)
        
    def prepare_dataset(
        self,
        texts: List[str],
        labels: List[int],
        max_length: int = 512
    ) -> Dataset:
        def tokenize_function(examples):
            return self.tokenizer(
                examples["text"],
                padding="max_length",
                truncation=True,
                max_length=max_length
            )
        
        dataset = Dataset.from_dict({"text": texts, "label": labels})
        tokenized = dataset.map(tokenize_function, batched=True)
        return tokenized
    
    def train(
        self,
        train_dataset: Dataset,
        eval_dataset: Optional[Dataset] = None,
        output_dir: str = "./berturk_education_model",
        epochs: int = 3,
        batch_size: int = 16,
        learning_rate: float = 2e-5
    ):
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=epochs,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            learning_rate=learning_rate,
            weight_decay=0.01,
            evaluation_strategy="epoch" if eval_dataset else "no",
            save_strategy="epoch",
            load_best_model_at_end=True if eval_dataset else False,
            logging_dir="./logs",
            logging_steps=10,
            fp16=torch.cuda.is_available()
        )
        
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            tokenizer=self.tokenizer,
            data_collator=DataCollatorWithPadding(self.tokenizer),
            compute_metrics=self._compute_metrics
        )
        
        trainer.train()
        return trainer
    
    def _compute_metrics(self, eval_pred):
        predictions, labels = eval_pred
        predictions = np.argmax(predictions, axis=1)
        
        precision, recall, f1, _ = precision_recall_fscore_support(
            labels, predictions, average="weighted"
        )
        acc = accuracy_score(labels, predictions)
        
        return {
            "accuracy": acc,
            "f1": f1,
            "precision": precision,
            "recall": recall
        }
    
    def predict(self, texts: List[str]) -> List[int]:
        inputs = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            return_tensors="pt"
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = torch.argmax(outputs.logits, dim=-1)
        
        return predictions.cpu().numpy().tolist()


class EducationDatasetBuilder:
    @staticmethod
    def build_difficulty_classification_dataset():
        # Example: Classify question difficulty
        texts = [
            "2 + 2 = ?",
            "x^2 + 5x + 6 = 0 denklemini cozunuz",
            "Integral of sin(x)dx",
            "Termodinamiðin ikinci yasasýný aciklayiniz"
        ]
        labels = [0, 2, 3, 4]  # 0=very easy, 4=very hard
        return texts, labels
    
    @staticmethod
    def build_topic_classification_dataset():
        # Classify educational topics
        texts = [
            "Pisagor teoremi ile dik ucgende kenar hesaplama",
            "Fotosentez surecinde klorofilin rolu",
            "Osmanli Imparatorluðunun kurulusu"
        ]
        labels = [0, 1, 2]  # 0=math, 1=biology, 2=history
        return texts, labels


# Model versioning and A/B testing
class ModelRegistry:
    def __init__(self):
        self.models: Dict[str, str] = {}
        self.active_model: str = "v1"
    
    def register_model(self, version: str, model_path: str):
        self.models[version] = model_path
    
    def set_active_model(self, version: str):
        if version in self.models:
            self.active_model = version
        else:
            raise ValueError(f"Model version {version} not found")
    
    def get_active_model_path(self) -> str:
        return self.models.get(self.active_model)
