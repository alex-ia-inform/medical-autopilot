import json
import os
import time
from datetime import datetime
import requests
from dotenv import load_dotenv

# Завантажуємо змінні оточення
load_dotenv()

# Конфігурація
MEDICAL_NEWS_FILE = 'medical_news.json'
HISTORY_FILE = 'published_history.json'
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def get_medical_news():
    """Отримує медичні новини (спрощена версія парсера)"""
    sources = [
        {"name": "ВООЗ Новини", "url": "https://www.who.int/news-room"},
        {"name": "PubMed", "url": "https://pubmed.ncbi.nlm.nih.gov/?term=medical+news&sort=pubdate&size=5"}
    ]
    
    articles = []
    try:
        # Отримуємо новини ВООЗ
        who_response = requests.get(sources[0]['url'], timeout=10)
        if who_response.status_code == 200:
            # Тут має бути логіка парсингу, але для прикладу використовуємо мок-дані
            articles.append({
                "title": "ВООЗ: Нові рекомендації щодо профілактики серцево-судинних захворювань",
                "link": "https://www.who.int/news/item/15-06-2025-new-cardiovascular-guidelines",
                "source": "ВООЗ"
            })
        
        # Отримуємо новини PubMed
        pubmed_response = requests.get(sources[1]['url'], timeout=10)
        if pubmed_response.status_code == 200:
            # Тут має бути логіка парсингу
            articles.append({
                "title": "Нове дослідження: Вплив мікропластику на здоров'я людини",
                "link": "https://pubmed.ncbi.nlm.nih.gov/123456789",
                "source": "PubMed"
            })
    
    except Exception as e:
        print(f"Помилка отримання новин: {e}")
    
    # Зберігаємо новини для подальшого використання
    with open(MEDICAL_NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    
    return articles

def generate_medical_post(news_title):
    """Генерує медичний пост за допомогою Groq API"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""
Ти професійний медичний журналіст. Створи інформативний пост для Telegram на основі цієї новини.

**Вимоги:**
- Мова: українська
- Обсяг: 3-4 речення
- Структура:
  1. Заголовок (з емодзі)
  2. Основні факти
  3. Чому це важливо?
- Додай дисклеймер: "Ця інформація не є медичною консультацією"

**Новина: {news_title}**
"""
    
    data = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": "Ти експерт з медичних новин"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 250
    }
    
    try:
        response = requests.post(GROQ_API_URL, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Помилка генерації поста: {e}")
        return None

def send_to_telegram(message):
    """Відправляє повідомлення в Telegram канал"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL:
        print("Помилка: Не налаштовані змінні Telegram")
        return False
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHANNEL,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return True
        else:
            print(f"Помилка Telegram API: {response.status_code}")
            return False
    except Exception as e:
        print(f"Помилка з'єднання з Telegram: {e}")
        return False

def load_published_history():
    """Завантажує історію опублікованих новин"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_published_history(history):
    """Зберігає історію опублікованих новин"""
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def main():
    print(f"=== Запуск медичного автопілота {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")
    
    # Завантажуємо історію опублікованих новин
    published_history = load_published_history()
    published_titles = [item['title'] for item in published_history]
    
    # Отримуємо новини
    print("Отримання медичних новин...")
    news = get_medical_news()
    print(f"Знайдено {len(news)} новин.")
    
    # Фільтруємо новини (лише нові)
    new_news = [item for item in news if item['title'] not in published_titles]
    print(f"Знайдено {len(new_news)} нових новин.")
    
    # Обробляємо новини (не більше 2 за раз)
    for item in new_news[:2]:
        print(f"\nОбробка новини: {item['title']}")
        
        # Генерація поста
        print("Генерація поста...")
        post_content = generate_medical_post(item['title'])
        
        if not post_content:
            print("Помилка генерації. Пропускаємо.")
            continue
            
        # Додаємо посилання на джерело
        full_post = f"{post_content}\n\nДжерело: {item['link']}"
        
        # Публікація в Telegram
        print("Публікація в Telegram...")
        if send_to_telegram(full_post):
            # Додаємо до історії
            published_history.append({
                "title": item['title'],
                "link": item['link'],
                "published_at": datetime.now().isoformat()
            })
            # Оновлюємо історію
            save_published_history(published_history)
            print("Успішно опубліковано!")
        else:
            print("Помилка публікації в Telegram.")
        
        # Пауза між постами
        time.sleep(10)
    
    print("\nАвтоматизація завершена!")

if __name__ == "__main__":
    main()