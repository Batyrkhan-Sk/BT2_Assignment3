import requests
from bs4 import BeautifulSoup
import json
import os
import re

def fetch_constitution():
    """
    Fetches the Constitution of Kazakhstan from the official website
    """
    url = "https://www.akorda.kz/en/constitution-of-the-republic-of-kazakhstan-50912"
    
    try:
        # Send GET request to the website
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Debug: Print all div classes to help identify the correct one
        print("Available div classes:")
        for div in soup.find_all('div', class_=True):
            print(f"Found div with class: {div['class']}")
        
        # Try to find the main content
        content = None
        possible_classes = ['content', 'text', 'article', 'main-content', 'constitution-content']
        
        for class_name in possible_classes:
            content = soup.find('div', class_=class_name)
            if content:
                print(f"Found content in div with class: {class_name}")
                break
        
        if not content:
            # If no specific class found, try to find content by structure
            content = soup.find('div', {'id': 'content'})
            if not content:
                content = soup.find('main')
            if not content:
                content = soup.find('article')
        
        if not content:
            raise Exception("Could not find the main content on the page")
        
        # Extract all articles
        articles = []
        current_article = None
        current_text = []
        
        # Find all text elements that might contain articles
        for element in content.find_all(['h2', 'h3', 'p', 'div']):
            text = element.text.strip()
            if not text:
                continue
                
            # Check if this is an article header
            if re.match(r'^Article \d+', text) or re.match(r'^Section [IV]+', text):
                # If we have a previous article, save it
                if current_article and current_text:
                    articles.append({
                        'title': current_article,
                        'content': ' '.join(current_text)
                    })
                    current_text = []
                
                # Start new article
                current_article = text
            else:
                # Add text to current article
                current_text.append(text)
        
        # Add the last article
        if current_article and current_text:
            articles.append({
                'title': current_article,
                'content': ' '.join(current_text)
            })
        
        if not articles:
            # If no articles found, try a different approach
            print("No articles found with first approach, trying alternative method...")
            # Look for any text that might be part of the constitution
            all_text = content.get_text(separator=' ', strip=True)
            if all_text:
                articles.append({
                    'title': 'Constitution of Kazakhstan',
                    'content': all_text
                })
        
        if not articles:
            raise Exception("No articles found in the content")
        
        # Save to JSON file
        with open('constitution.json', 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        
        print(f"Successfully fetched and saved {len(articles)} articles from the Constitution")
        return articles
        
    except requests.RequestException as e:
        print(f"Error fetching the constitution: {e}")
        return None
    except Exception as e:
        print(f"Error processing the constitution: {e}")
        return None

def read_constitution():
    """
    Reads the saved constitution from the JSON file
    """
    try:
        if not os.path.exists('constitution.json'):
            print("Constitution file not found. Fetching from website...")
            return fetch_constitution()
        
        with open('constitution.json', 'r', encoding='utf-8') as f:
            articles = json.load(f)
        
        return articles
    except Exception as e:
        print(f"Error reading the constitution: {e}")
        return None

def search_constitution(query):
    """
    Searches through the constitution for specific terms and returns relevant articles
    """
    articles = read_constitution()
    if not articles:
        return []
    
    query = query.lower()
    found_articles = []
    
    for article in articles:
        if query in article['title'].lower() or query in article['content'].lower():
            found_articles.append(article)
    
    return found_articles

def format_response(articles, query):
    """
    Formats the response in a chat-like manner
    """
    if not articles:
        return f"I couldn't find any specific provisions in the Constitution of Kazakhstan that directly address '{query}'. The Constitution primarily outlines the fundamental principles of the state, rights and freedoms of citizens, and the structure of government. For specific matters, you would need to refer to the relevant laws and regulations of Kazakhstan."
    
    response = f"Based on the Constitution of Kazakhstan, here are the relevant provisions:\n\n"
    
    for article in articles:
        response += f"{article['title']}\n"
        response += "-" * len(article['title']) + "\n"
        response += f"{article['content']}\n\n"
    
    return response

def chat_interface():
    """
    Provides a chat-like interface for querying the constitution
    """
    print("Welcome to the Constitution of Kazakhstan Chat Assistant!")
    print("Type 'exit' to quit the chat.")
    print("\nAsk a question about the Constitution of Kazakhstan:")
    
    while True:
        query = input("\nYou: ").strip()
        
        if query.lower() == 'exit':
            print("\nGoodbye!")
            break
        
        if not query:
            continue
        
        articles = search_constitution(query)
        response = format_response(articles, query)
        print(f"\nAssistant: {response}")

if __name__ == "__main__":
    chat_interface() 