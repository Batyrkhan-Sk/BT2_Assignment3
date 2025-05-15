import requests
from bs4 import BeautifulSoup
import json
import os
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_constitution():
    """
    Fetches the Constitution of Kazakhstan from the official website
    """
    url = "https://www.akorda.kz/en/constitution-of-the-republic-of-kazakhstan-50912"
    
    try:
        # Send GET request to the website
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the main content
        content = None
        possible_classes = ['content', 'text', 'article', 'main-content', 'constitution-content']
        
        for class_name in possible_classes:
            content = soup.find('div', class_=class_name)
            if content:
                logger.info(f"Found content in div with class: {class_name}")
                break
        
        if not content:
            # Try alternative content locations
            content = soup.find('div', {'id': 'content'}) or soup.find('main') or soup.find('article')
        
        if not content:
            raise Exception("Could not find the main content on the page")
        
        # Extract all articles with improved parsing
        articles = []
        current_article = None
        current_section = None
        current_text = []
        
        # Find all text elements that might contain articles
        for element in content.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'div']):
            text = element.text.strip()
            if not text:
                continue
            
            # Check for article headers
            article_match = re.match(r'^Article (\d+)', text)
            section_match = re.match(r'^Section ([IV]+)', text)
            
            if article_match:
                # Save previous article if exists
                if current_article and current_text:
                    articles.append({
                        'title': current_article,
                        'section': current_section,
                        'content': ' '.join(current_text),
                        'article_number': int(article_match.group(1))
                    })
                    current_text = []
                
                # Start new article
                current_article = text
                current_section = None
            elif section_match:
                # Save previous section if exists
                if current_article and current_text:
                    articles.append({
                        'title': current_article,
                        'section': current_section,
                        'content': ' '.join(current_text),
                        'article_number': int(re.search(r'Article (\d+)', current_article).group(1))
                    })
                    current_text = []
                
                current_section = text
            else:
                # Add text to current article
                current_text.append(text)
        
        # Add the last article
        if current_article and current_text:
            articles.append({
                'title': current_article,
                'section': current_section,
                'content': ' '.join(current_text),
                'article_number': int(re.search(r'Article (\d+)', current_article).group(1))
            })
        
        if not articles:
            raise Exception("No articles found in the content")
        
        # Save to JSON file
        with open('constitution.json', 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Successfully fetched and saved {len(articles)} articles from the Constitution")
        return articles
        
    except requests.RequestException as e:
        logger.error(f"Error fetching the constitution: {e}")
        return None
    except Exception as e:
        logger.error(f"Error processing the constitution: {e}")
        return None

def read_constitution():
    """
    Reads the saved constitution from the JSON file
    """
    try:
        if not os.path.exists('constitution.json'):
            logger.info("Constitution file not found. Fetching from website...")
            return fetch_constitution()
        
        with open('constitution.json', 'r', encoding='utf-8') as f:
            articles = json.load(f)
        
        return articles
    except Exception as e:
        logger.error(f"Error reading the constitution: {e}")
        return None

def search_constitution(query):
    """
    Enhanced search through the constitution for specific terms and returns relevant articles
    """
    articles = read_constitution()
    if not articles:
        return []
    
    query = query.lower()
    found_articles = []
    
    # Split query into keywords
    keywords = query.split()
    
    for article in articles:
        # Check title and content
        title_lower = article['title'].lower()
        content_lower = article['content'].lower()
        
        # Calculate relevance score
        relevance_score = 0
        
        # Check for exact matches
        if query in title_lower:
            relevance_score += 3
        if query in content_lower:
            relevance_score += 2
        
        # Check for keyword matches
        for keyword in keywords:
            if keyword in title_lower:
                relevance_score += 1
            if keyword in content_lower:
                relevance_score += 0.5
        
        # Add article if it has any relevance
        if relevance_score > 0:
            article['relevance_score'] = relevance_score
            found_articles.append(article)
    
    # Sort by relevance score
    found_articles.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    return found_articles

def format_response(articles, query):
    """
    Enhanced response formatting with better structure and readability
    """
    if not articles:
        return f"I couldn't find any specific provisions in the Constitution of Kazakhstan that directly address '{query}'. The Constitution primarily outlines the fundamental principles of the state, rights and freedoms of citizens, and the structure of government. For specific matters, you would need to refer to the relevant laws and regulations of Kazakhstan."
    
    response = f"Based on the Constitution of Kazakhstan, here are the relevant provisions:\n\n"
    
    for article in articles:
        # Add section if it exists
        if article.get('section'):
            response += f"{article['section']}\n"
            response += "-" * len(article['section']) + "\n"
        
        # Add article title and content
        response += f"{article['title']}\n"
        response += "-" * len(article['title']) + "\n"
        
        # Format content with better paragraph separation
        content = article['content']
        paragraphs = content.split('. ')
        formatted_content = '.\n'.join(paragraphs)
        response += f"{formatted_content}\n\n"
    
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