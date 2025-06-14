import json
import requests
import os
from dotenv import load_dotenv
import time

load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")
API_URL = "https://api.groq.com/openai/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def generate_medical_post(news_title):
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
        response = requests.post(API_URL, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Помилка: {str(e)}")
        if response.status_code == 429:
            print("Досягнуто ліміт запитів. Зачекайте 1 хвилину.")
            time.sleep(60)
        return ""

# Тестова новина
test_news = {
    "title": "Нові дослідження про користь вітаміну D для імунітету",
    "source": "Тест"
}

print("Тест генерації...")
post = generate_medical_post(test_news['title'])

if post:
    print("\n=== ЗГЕНЕРОВАНИЙ ПОСТ ===")
    print(post)
    
    # Збереження результату
    with open('groq_post.txt', 'w', encoding='utf-8') as f:
        f.write(post)
    print("\nРезультат збережено у groq_post.txt")
else:
    print("Не вдалося згенерувати пост. Перевірте API ключ.")