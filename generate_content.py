import json
from openai import OpenAI
import os
from dotenv import load_dotenv
import time

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_medical_post(news_item):
    """Генерує медичний пост на основі новини"""
    prompt = f"""
Ти експерт з медичних новин. Створи інформативний пост для соціальних мереж на основі цієї новини.
**Вимоги:**
- Мова: українська
- Обсяг: 180-250 слів
- Структура:
  1. Заголовок (з емоційним емоційним емодзі)
  2. Основна інформація (ключові факти)
  3. Значення/наслідки (чому це важливо?)
  4. Посилання на джерело
- Уникай медичних діагнозів та порад щодо лікування
- Додай дисклеймер: "Ця інформація не є медичною консультацією"

**Новина:**
{news_item['title']}
{news_item.get('summary', '')}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ти професійний медичний журналіст."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=450
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Помилка генерації: {e}")
        return ""

# Завантажуємо новини з файлу
with open('medical_news.json', 'r', encoding='utf-8') as f:
    medical_news = json.load(f)

# Генеруємо пости для перших 3 новин (тест)
generated_posts = []
for i, news in enumerate(medical_news[:3]):
    print(f"Генеруємо пост для новини #{i+1}: {news['title'][:50]}...")
    post_content = generate_medical_post(news)
    
    if post_content:
        generated_posts.append({
            "original_title": news['title'],
            "generated_content": post_content,
            "source": news['source'],
            "link": news['link']
        })
        print(f"Успішно згенеровано пост!\n---\n{post_content}\n---")
    else:
        print("Не вдалося згенерувати пост")
    
    # Пауза між запитами
    time.sleep(2)

# Зберігаємо результати
with open('generated_posts.json', 'w', encoding='utf-8') as f:
    json.dump(generated_posts, f, ensure_ascii=False, indent=2)

print("Генерація завершена. Результати збережено у generated_posts.json")