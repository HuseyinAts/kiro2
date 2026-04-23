# Training script for BERTurk Education Domain Fine-tuning

from berturk_finetuning_pipeline import (
    BERTurkEducationFineTuner,
    EducationDatasetBuilder,
)


def main():
    print('Starting BERTurk Education Domain Fine-tuning...')

    # Initialize fine-tuner
    finetuner = BERTurkEducationFineTuner(
        base_model="dbmdz/bert-base-turkish-cased",
        num_labels=5  # Difficulty levels: very easy, easy, medium, hard, very hard
    )

    # Build dataset
    texts, labels = EducationDatasetBuilder.build_difficulty_classification_dataset()

    # Prepare training data
    train_dataset = finetuner.prepare_dataset(texts, labels)

    # Train model
    print('Training model...')
    trainer = finetuner.train(
        train_dataset=train_dataset,
        output_dir="./models/berturk_education_v1",
        epochs=3,
        batch_size=8,
        learning_rate=2e-5
    )

    # Save model
    trainer.save_model("./models/berturk_education_v1")
    print('Model saved to ./models/berturk_education_v1')

    # Test predictions
    test_texts = [
        "3 + 5 = ?",
        "Turevleri kullanarak maksimum nokta bulma"
    ]
    predictions = finetuner.predict(test_texts)
    print(f'Test predictions: {predictions}')


if __name__ == '__main__':
    main()
