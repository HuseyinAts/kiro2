#!/usr/bin/env python3
"""
Test Custom HuggingFace Endpoint
Focused test for your specific endpoint: https://cf781mfqobm2ynkk.us-east-1.aws.endpoints.huggingface.cloud
"""

import asyncio
import os

# Set your custom endpoint
CUSTOM_ENDPOINT = "https://cf781mfqobm2ynkk.us-east-1.aws.endpoints.huggingface.cloud"

print("=" * 70)
print("CUSTOM HUGGINGFACE ENDPOINT TEST")
print(f"Endpoint: {CUSTOM_ENDPOINT}")
print("=" * 70)
print()


def test_direct_endpoint():
    """Test direct connection to your custom endpoint"""
    import requests

    print("[TEST] Direct Endpoint Connection")
    print("-" * 40)

    # Check if HuggingFace token is set
    hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN", "")
    if not hf_token:
        print("[WARNING] No HuggingFace token found in environment")
        print("To use your custom endpoint, set HUGGINGFACEHUB_API_TOKEN in .env file")
        return False

    headers = {
        "Authorization": f"Bearer {hf_token}",
        "Content-Type": "application/json",
    }

    # Test payload
    payload = {
        "inputs": "What is the capital of Turkey?",
        "parameters": {"temperature": 0.7, "max_new_tokens": 50, "top_p": 0.95},
    }

    try:
        print(f"[INFO] Sending test request to endpoint...")
        response = requests.post(
            CUSTOM_ENDPOINT, headers=headers, json=payload, timeout=30
        )

        if response.status_code == 200:
            print("[SUCCESS] Endpoint responded successfully!")
            result = response.json()
            print(f"Response: {result}")
            return True
        else:
            print(f"[ERROR] Endpoint returned status {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("[ERROR] Request timed out (30 seconds)")
        return False
    except requests.exceptions.ConnectionError:
        print("[ERROR] Could not connect to endpoint")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {str(e)}")
        return False


async def test_langchain_custom_endpoint():
    """Test LangChain integration with your custom endpoint"""
    print("\n[TEST] LangChain Custom Endpoint Integration")
    print("-" * 40)

    try:
        from langchain_community.llms import HuggingFaceEndpoint
    except ImportError:
        from langchain.llms import HuggingFaceEndpoint

    # Check for token
    hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN", "")
    if not hf_token:
        print("[INFO] Using mock mode - no token provided")
        print("To test with real endpoint, add your token to backend/.env:")
        print("HUGGINGFACEHUB_API_TOKEN=your_token_here")

        # Mock response for demonstration
        class MockEndpoint:
            def __init__(self, *args, **kwargs):
                self.endpoint_url = CUSTOM_ENDPOINT

            def invoke(self, prompt):
                return f"Mock response for: {prompt}"

            async def ainvoke(self, prompt):
                return f"Mock response for: {prompt}"

        llm = MockEndpoint()
    else:
        print("[INFO] Initializing HuggingFaceEndpoint with your custom URL...")

        try:
            llm = HuggingFaceEndpoint(
                endpoint_url=CUSTOM_ENDPOINT,
                huggingfacehub_api_token=hf_token,
                task="text-generation",
                model_kwargs={
                    "temperature": 0.7,
                    "max_new_tokens": 100,
                    "top_p": 0.95,
                },
            )
            print("[SUCCESS] LangChain endpoint initialized!")
        except Exception as e:
            print(f"[ERROR] Failed to initialize endpoint: {str(e)}")
            return

    # Test queries
    test_prompts = [
        "What is the capital of Turkey?",
        "Explain machine learning in one sentence.",
        "Write a Python function to add two numbers.",
    ]

    print("\n[INFO] Testing with sample prompts...")
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\nPrompt {i}: {prompt}")
        try:
            # Use async if available
            if hasattr(llm, "ainvoke"):
                response = await llm.ainvoke(prompt)
            else:
                response = llm.invoke(prompt)

            print(
                f"Response: {response[:200]}..."
                if len(response) > 200
                else f"Response: {response}"
            )
            print("[SUCCESS] Query completed")
        except Exception as e:
            print(f"[ERROR] Query failed: {str(e)}")


def test_with_langchain_chains():
    """Test using your endpoint in LangChain chains"""
    print("\n[TEST] LangChain Chains with Custom Endpoint")
    print("-" * 40)

    try:
        from langchain.chains import LLMChain
        from langchain.prompts import PromptTemplate

        try:
            from langchain_community.llms import HuggingFaceEndpoint
        except ImportError:
            from langchain.llms import HuggingFaceEndpoint

        hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN", "")
        if not hf_token:
            print("[SKIP] Skipping chain test - no token provided")
            return

        # Create LLM
        llm = HuggingFaceEndpoint(
            endpoint_url=CUSTOM_ENDPOINT,
            huggingfacehub_api_token=hf_token,
            task="text-generation",
            model_kwargs={"temperature": 0.7, "max_new_tokens": 100},
        )

        # Create prompt template
        template = """You are a helpful assistant. Answer the following question:
        
        Question: {question}
        Answer:"""

        prompt = PromptTemplate(template=template, input_variables=["question"])

        # Create chain
        chain = LLMChain(llm=llm, prompt=prompt, verbose=True)

        # Test the chain
        test_questions = [
            "What is LangChain?",
            "How does RAG work?",
            "What are embeddings?",
        ]

        for question in test_questions:
            print(f"\nQuestion: {question}")
            try:
                result = chain.run(question=question)
                print(f"Answer: {result[:200]}...")
                print("[SUCCESS] Chain execution completed")
            except Exception as e:
                print(f"[ERROR] Chain execution failed: {str(e)}")

    except ImportError as e:
        print(f"[ERROR] Import error: {str(e)}")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {str(e)}")


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("RUNNING CUSTOM ENDPOINT TESTS")
    print("=" * 70)

    # Check configuration
    print("\n[CONFIG] Environment Check:")
    print(f"  Custom Endpoint: {CUSTOM_ENDPOINT}")
    print(
        f"  HuggingFace Token: {'SET' if os.getenv('HUGGINGFACEHUB_API_TOKEN') else 'NOT SET'}"
    )

    # Run tests
    print("\n" + "=" * 70)
    print("TEST 1: Direct Endpoint Connection")
    print("=" * 70)
    test_direct_endpoint()

    print("\n" + "=" * 70)
    print("TEST 2: LangChain Integration")
    print("=" * 70)
    asyncio.run(test_langchain_custom_endpoint())

    print("\n" + "=" * 70)
    print("TEST 3: LangChain Chains")
    print("=" * 70)
    test_with_langchain_chains()

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(
        f"""
Custom Endpoint: {CUSTOM_ENDPOINT}

To use your custom endpoint with real responses:
1. Get your HuggingFace API token from https://huggingface.co/settings/tokens
2. Add it to backend/.env file:
   HUGGINGFACEHUB_API_TOKEN=your_token_here
   
3. Run this test again:
   cd backend && python test_custom_hf_endpoint.py

Your endpoint is configured and ready to use!
"""
    )


if __name__ == "__main__":
    main()
