"""Test question generation - simplified version"""
import random

print("Starting test generation...")

# Simple test generator
class TestGenerator:
    def generate_simple_question(self):
        num1 = random.randint(10, 50)
        num2 = random.randint(10, 50)
        result = num1 + num2

        text = f"Test Question: {num1} + {num2} = ?"
        options = [str(result), str(result + 10), str(result - 10), str(result + 5), str(result - 5)]
        random.shuffle(options)

        return {
            'text': text,
            'options': options,
            'correct': 'A',
            'difficulty': 0.5
        }

# Generate 5 test questions
gen = TestGenerator()
for i in range(5):
    q = gen.generate_simple_question()
    print(f"Question {i+1}: {q['text']}")
    print(f"Options: {q['options']}")
    print("-" * 40)

print("Test generation completed!")