import requests
from bs4 import BeautifulSoup
import re
import time
import json
import random

# Вимкнути перевірку SSL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Надійні джерела медичних новин
MEDICAL_SOURCES = [
    {
        'name': 'ВООЗ Новини',
        'url': 'https://www.who.int/news-room',
        'type': 'html'
    },
    {
        'name': 'Medscape Headlines',
        'url': 'https://www.medscape.com/headlines',
        'type': 'html'
    },
    {
        'name': 'PubMed Medical News',
        'url': 'https://pubmed.ncbi.nlm.nih.gov/?term=medical+news&sort=pubdate&size=10',
        'type': 'html'
    },
    {
        'name': 'Medical News Today',
        'url': 'https://www.medicalnewstoday.com/news',
        'type': 'html'
    }
]

def clean_text(text):
    """Очищення тексту від зайвих пробілів та символів"""
    if text is None:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def get_random_user_agent():
    """Генерація випадкового User-Agent"""
    agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (iPad; CPU OS 13_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1'
    ]
    return random.choice(agents)

def parse_html_source(source):
    """Парсинг HTML-джерел"""
    print(f"\nПарсим: {source['name']} ({source['url']})")
    articles = []
    
    try:
        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'uk-UA,uk;q=0.9,ru;q=0.8,en-US;q=0.7,en;q=0.6',
            'Referer': 'https://www.google.com/'
        }
        
        response = requests.get(source['url'], headers=headers, timeout=15, verify=False)
        response.encoding = 'utf-8'
        print(f"  Статус: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Специфічні правила парсингу для кожного джерела
        if 'who.int' in source['url']:
            # ВООЗ - Newsroom
            for item in soup.select('.list-view--item'):
                title_elem = item.select_one('.heading')
                if not title_elem: continue
                
                title = clean_text(title_elem.text)
                link = "https://www.who.int" + item.find('a')['href']
                
                date_elem = item.select_one('.timestamp')
                date = clean_text(date_elem.text) if date_elem else ""
                
                articles.append({
                    'title': title,
                    'link': link,
                    'published': date,
                    'summary': "",
                    'source': source['name']
                })
        
        elif 'medscape.com' in source['url']:
            # Medscape Headlines
            for item in soup.select('.headline'):
                title_elem = item.select_one('a')
                if not title_elem: continue
                
                title = clean_text(title_elem.text)
                link = "https://www.medscape.com" + title_elem['href']
                
                articles.append({
                    'title': title,
                    'link': link,
                    'published': "",
                    'summary': "",
                    'source': source['name']
                })
        
        elif 'pubmed' in source['url']:
            # PubMed
            for item in soup.select('.docsum-content'):
                title_elem = item.select_one('.docsum-title')
                if not title_elem: continue
                
                title = clean_text(title_elem.text)
                link = "https://pubmed.ncbi.nlm.nih.gov" + title_elem['href']
                
                date_elem = item.select_one('.docsum-journal-citation')
                date = clean_text(date_elem.text) if date_elem else ""
                
                articles.append({
                    'title': title,
                    'link': link,
                    'published': date,
                    'summary': "",
                    'source': source['name']
                })
        
        elif 'medicalnewstoday.com' in source['url']:
            # Medical News Today
            for item in soup.select('article'):
                title_elem = item.select_one('h2 a')
                if not title_elem: continue
                
                title = clean_text(title_elem.text)
                link = title_elem['href']
                
                date_elem = item.select_one('time')
                date = clean_text(date_elem['datetime']) if date_elem else ""
                
                articles.append({
                    'title': title,
                    'link': link,
                    'published': date,
                    'summary': "",
                    'source': source['name']
                })
        
        print(f"  Знайдено новин: {len(articles)}")
        return articles
    
    except Exception as e:
        print(f"  Помилка парсингу: {str(e)}")
        return []

def get_medical_news():
    """Отримання всіх медичних новин"""
    print("\n=== ЗАПУСК МЕДИЧНОГО ПАРСЕРА ===")
    all_articles = []
    
    for source in MEDICAL_SOURCES:
        if source['type'] == 'html':
            articles = parse_html_source(source)
            all_articles.extend(articles)
    
    return all_articles

if __name__ == "__main__":
    start_time = time.time()
    news = get_medical_news()
    elapsed = time.time() - start_time
    
    print(f"\n=== РЕЗУЛЬТАТ ===")
    print(f"Знайдено {len(news)} медичних новин (час: {elapsed:.2f} сек)")
    
    if news:
        # Зберегти результати у файл
        with open('medical_news.json', 'w', encoding='utf-8') as f:
            json.dump(news, f, ensure_ascii=False, indent=2)
        
        print("\nПерші 5 новин:")
        for i, item in enumerate(news[:5], 1):
            print(f"\n{i}. [{item['source']}] {item['title']}")
            print(f"   Посилання: {item['link']}")
            if item['published']:
                print(f"   Дата: {item['published']}")
    else:
        print("Новин не знайдено. Перевірте налаштування парсера.")