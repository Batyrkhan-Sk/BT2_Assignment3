import ollama
import sys
import traceback

def test_ollama_detailed():
    print("Starting Ollama connection test...")
    
    try:
        print("1. Initializing Ollama client...")
        client = ollama.Client(host='http://localhost:11434')
        print("✓ Client initialized successfully")
        
        print("\n2. Getting model list...")
        models = client.list()
        print("Models available:", models)
        
        print("\n3. Testing model availability...")
        if not any('llama2' in model.model for model in models.models):
            print("❌ llama2 model not found!")
            return False
        print("✓ llama2 model found")
        
        print("\n4. Testing simple chat completion...")
        response = client.chat(
            model='llama2',
            messages=[{'role': 'user', 'content': 'Say hello'}],
            options={'temperature': 0.7, 'num_predict': 10}
        )
        print("Response received:", response)
        print("✓ Chat completion successful")
        
        return True
        
    except Exception as e:
        print("\n❌ Error occurred!")
        print("Error type:", type(e).__name__)
        print("Error message:", str(e))
        print("\nTraceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Python version:", sys.version)
    print("\nStarting tests...\n")
    
    success = test_ollama_detailed()
    
    if success:
        print("\n✅ All tests passed successfully!")
    else:
        print("\n❌ Tests failed!") 