import requests
import json
from bs4 import BeautifulSoup

URL = 'https://ria.ru/world/'
r = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0'})
soup = BeautifulSoup(r.text, 'lxml')

def get_news():
    items_list = soup.find_all('div', class_='list-item')[:7]

    news = []  # Список для хранения новостей

    for item in items_list:
        title_elem = item.find('a', class_='list-item__title')
        img_elem = item.find('img')
        link_elem = item.find('a', class_='list-item__image')

        if title_elem and link_elem:
            card = {
                'text': title_elem.text.strip(),
                'img': img_elem['src'] if img_elem else None,
                'src': link_elem['href']
            }
            news.append(card)

    # Запись всех новостей в JSON-файл
    with open('news.json', 'w', encoding='utf-8') as file:
        json.dump(news, file, indent=4, ensure_ascii=False)
