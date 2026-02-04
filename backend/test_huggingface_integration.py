#!/usr/bin/env python
"""
Test HuggingFace Endpoint Integration
This script tests the HuggingFace endpoint integration for the AI Education Platform
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Import the LLM service
from core.llm_service import llm_service


async def test_basic_generation():
    """Test basic text generation"""
    print("\n=== Testing Basic Text Generation ===")

    prompts = [
        "Python programlama dili nedir?",
        "LGS sınavına nasıl hazırlanmalıyım?",
        "Matematik öğrenmenin en etkili yolu nedir?",
    ]

    for prompt in prompts:
        print(f"\nPrompt: {prompt}")
        print("-" * 50)

        result = await llm_service.generate(
            prompt=prompt, max_tokens=200, temperature=0.7
        )

        if result["success"]:
            print(f"Response: {result['text'][:500]}...")  # Limit output length
            print(f"Model: {result['metadata']['model']}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")


async def test_educational_tasks():
    """Test educational-specific tasks"""
    print("\n=== Testing Educational Tasks ===")

    tasks = [
        ("question_generation", "Fotosentez konusu"),
        (
            "summarization",
            "Python programlama dili, yüksek seviyeli, genel amaçlı bir dildir. Guido van Rossum tarafından 1991 yılında geliştirilmiştir.",
        ),
        (
            "flashcard_generation",
            "Türkiye'nin başkenti Ankara'dır. Türkiye'nin en büyük şehri İstanbul'dur.",
        ),
    ]

    for task_type, content in tasks:
        print(f"\nTask: {task_type}")
        print(f"Content: {content[:100]}...")
        print("-" * 50)

        result = await llm_service.generate_for_education(
            task_type=task_type, content=content
        )

        if result["success"]:
            print(f"Response: {result['content'][:500]}...")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")


async def test_chat():
    """Test chat conversation"""
    print("\n=== Testing Chat Conversation ===")

    messages = [
        {"role": "user", "content": "Merhaba, ben 8. sınıf öğrencisiyim"},
        {
            "role": "assistant",
            "content": "Merhaba! 8. sınıf öğrencisi olarak LGS'ye hazırlanıyor olmalısın. Sana nasıl yardımcı olabilirim?",
        },
        {"role": "user", "content": "Matematik konularında zorlanıyorum"},
    ]

    print("Conversation:")
    for msg in messages:
        print(f"{msg['role'].capitalize()}: {msg['content']}")
    print("-" * 50)

    result = await llm_service.chat(messages=messages)

    if result["success"]:
        print(f"Response: {result['text'][:500]}...")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")


async def test_agents():
    """Test agent integration"""
    print("\n=== Testing Agent Integration ===")

    from agents import ExamAgent, LearningAgent, StudyAgent

    agents = {
        "learning": (LearningAgent(), "Python öğrenmek istiyorum"),
        "study": (StudyAgent(), "Fotosentez nedir açıklar mısın?"),
        "exam": (ExamAgent(), "LGS matematik için nasıl çalışmalıyım?"),
    }

    for agent_name, (agent, message) in agents.items():
        print(f"\n{agent_name.capitalize()} Agent:")
        print(f"Message: {message}")
        print("-" * 50)

        response = await agent.process(message)
        print(f"Response: {response[:500]}...")


async def main():
    """Main test function"""
    print("\n" + "=" * 60)
    print("   HuggingFace Endpoint Integration Test")
    print("=" * 60)

    endpoint = os.getenv("HUGGINGFACE_ENDPOINT", "not configured")
    token_configured = "Yes" if os.getenv("HUGGINGFACE_API_TOKEN") else "No"
    use_mock = os.getenv("USE_MOCK_RESPONSES", "false").lower() == "true"

    print(f"\nConfiguration:")
    print(f"- Endpoint: {endpoint}")
    print(f"- Token Configured: {token_configured}")
    print(f"- Use Mock Responses: {use_mock}")
    print(f"- Python Version: {sys.version}")

    if endpoint == "not configured":
        print("\n⚠️  Warning: HUGGINGFACE_ENDPOINT not configured!")
        print(
            "Using default endpoint: https://cf781mfqobm2ynkk.us-east-1.aws.endpoints.huggingface.cloud"
        )

    # Run tests
    try:
        await test_basic_generation()
        await test_educational_tasks()
        await test_chat()
        await test_agents()

        print("\n" + "=" * 60)
        print("   [CHECK] All tests completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n[X] Test failed: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
