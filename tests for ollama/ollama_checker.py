#!/usr/bin/env python3
import requests
import time

print("\n" + "="*50)
print("OLLAMA QUICK DIAGNOSTIC")
print("="*50)

# Test 1: Running?
print("\n1. Is Ollama running?")
try:
    requests.get("http://localhost:11434/api/tags", timeout=2)
    print("   ✅ YES")
except:
    print("   ❌ NO - Start with: ollama serve")
    exit(1)

# Test 2: Models loaded?
print("\n2. Models available?")
try:
    r = requests.get("http://localhost:11434/api/tags")
    models = r.json()["models"]
    if models:
        for m in models:
            print(f"   ✅ {m['name']}")
    else:
        print("   ⚠️ No models (Run: ollama pull mistral:7b)")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Speed?
print("\n3. Response speed?")
try:
    payload = {"model": "mistral:7b", "prompt": "Hi", "stream": False}
    start = time.time()
    r = requests.post("http://localhost:11434/api/generate", json=payload, timeout=50)
    elapsed = time.time() - start
    result = r.json()
    tokens = result.get('eval_count', 0)
    print(f"   ✅ {elapsed:.2f}s ({tokens} tokens)")
    if elapsed > 10:
        print("      ⚠️ SLOW - Check GPU/resources")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*50)
print("Run this if all checks pass: python3 2hour_priorities.py")
print("="*50 + "\n")