#!/usr/bin/env python3
"""
Test script to verify Ollama + Qwen3-VL integration
Run: python test_ollama.py
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_ollama_connection():
    """Test if Ollama is running"""
    print("=" * 60)
    print("Testing Ollama Connection")
    print("=" * 60)

    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")

    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code == 200:
            print(f"✅ Ollama is running at {ollama_url}")

            models = response.json().get("models", [])
            print(f"\n📦 Available models: {len(models)}")
            for model in models:
                print(f"   - {model['name']}")

            return True
        else:
            print(f"❌ Ollama responded with status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to Ollama at {ollama_url}")
        print("\n💡 Make sure Ollama is running:")
        print("   ollama serve")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_model_availability():
    """Test if the configured model is available"""
    print("\n" + "=" * 60)
    print("Testing Model Availability")
    print("=" * 60)

    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5-vl:8b")

    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]

            if ollama_model in model_names:
                print(f"✅ Model '{ollama_model}' is installed")
                return True
            else:
                print(f"❌ Model '{ollama_model}' is not installed")
                print(f"\n💡 Available models: {', '.join(model_names)}")
                print(f"\n💡 To install the model, run:")
                print(f"   ollama pull {ollama_model}")
                return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_model_inference():
    """Test basic inference with the model"""
    print("\n" + "=" * 60)
    print("Testing Model Inference")
    print("=" * 60)

    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5-vl:8b")

    # Simple text-only test
    payload = {
        "model": ollama_model,
        "prompt": "Say 'OK' if you can read this.",
        "stream": False
    }

    try:
        print(f"Sending test prompt to {ollama_model}...")
        response = requests.post(
            f"{ollama_url}/api/generate",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            response_text = result.get("response", "")
            print(f"✅ Model responded: {response_text.strip()}")
            print(f"   Inference time: {result.get('total_duration', 0) / 1e9:.2f}s")
            return True
        else:
            print(f"❌ Request failed with status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print("❌ Request timed out (model might be loading)")
        print("💡 First request can take longer as the model loads into memory")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_ai_service():
    """Test the AIProctorService"""
    print("\n" + "=" * 60)
    print("Testing AIProctorService Integration")
    print("=" * 60)

    try:
        from ai_service import AIProctorService

        service = AIProctorService()
        print(f"✅ AIProctorService initialized")
        print(f"   Using Ollama: {service.use_ollama}")
        print(f"   Ollama URL: {service.ollama_url}")
        print(f"   Model: {service.ollama_model}")
        print(f"   Confidence Threshold: {service.confidence_threshold}")

        # Test with a dummy base64 image (1x1 white pixel)
        dummy_image = "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoHBwYIDAoMDAsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8XGBYUGBIUFRT/wAALCAABAAEBAREA/8QAFAABAAAAAAAAAAAAAAAAAAAACP/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AKp//2Q=="

        print("\nTesting frame analysis with dummy image...")
        is_suspicious, analysis = service.analyze_frame(dummy_image)

        print(f"✅ Analysis completed")
        print(f"   Is Suspicious: {is_suspicious}")
        print(f"   Analysis: {json.dumps(analysis, indent=2)}")

        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n🔍 Ollama + Qwen3-VL Integration Test\n")

    tests = [
        ("Ollama Connection", test_ollama_connection),
        ("Model Availability", test_model_availability),
        ("Model Inference", test_model_inference),
        ("AIProctorService", test_ai_service),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Your Ollama setup is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
