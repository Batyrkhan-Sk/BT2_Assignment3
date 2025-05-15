import ollama

def test_ollama():
    try:
        # Initialize client
        client = ollama.Client(host='http://localhost:11434')
        
        # Test simple chat
        response = client.chat(
            model='llama2',
            messages=[{'role': 'user', 'content': 'Say hello'}],
            options={'temperature': 0.7, 'num_predict': 10}
        )
        
        print("Connection successful!")
        print("Response:", response['message']['content'])
        return True
    except Exception as e:
        print("Error:", str(e))
        return False

if __name__ == "__main__":
    test_ollama() 