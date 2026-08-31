import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# Базовый URL для реестра АТС (Аттестованные технологии сварки). 
# Внимание: возможно потребуется уточнить актуальный адрес (например, через API сайта)
NAKS_ATS_URL = "https://naks.ru/registry/ats/"

def fetch_page(page_number):
    """Функция для загрузки определенной страницы реестра"""
    params = {
        'page': page_number,
        # Если на сайте есть фильтры через URL, можно передать их здесь
    }
    # Часто сайты требуют заголовки, чтобы не блокировать запросы как ботов
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    response = requests.get(NAKS_ATS_URL, params=params, headers=headers)
    response.raise_for_status()
    return response.text

def parse_page(html):
    """Функция для парсинга HTML и извлечения данных"""
    soup = BeautifulSoup(html, 'html.parser')
    
    records = []
    
    # ВАЖНО: Замените селекторы ниже на актуальные (нужно посмотреть код элемента на странице НАКС).
    # Этот пример предполагает, что данные лежат в таблице <table> и строках <tr>.
    table = soup.find('table') 
    
    if not table:
        return records

    # Пропускаем заголовок таблицы
    rows = table.find_all('tr')[1:] 

    for row in rows:
        cols = row.find_all('td')
        if len(cols) > 4: 
            # Пример извлечения данных (индексы колонок необходимо скорректировать под реальную таблицу)
            date_issue = cols[1].text.strip()
            equipment_brand = cols[3].text.strip()
            opo_type = cols[4].text.strip()
            
            # Проверяем, что свидетельство выдано в 2024 году
            if "2024" in date_issue:
                records.append({
                    'equipment_brand': equipment_brand,
                    'opo_type': opo_type
                })
                
    return records

def main():
    print("Начинаем сбор данных с сайта НАКС за 2024 год...")
    all_records = []
    
    # Пример обхода первых 5 страниц
    for page in range(1, 6):
        print(f"Парсинг страницы {page}...")
        try:
            html = fetch_page(page)
            page_records = parse_page(html)
            
            if not page_records:
                print("Данные не найдены (возможно конец списка или изменилась структура сайта).")
                break
                
            all_records.extend(page_records)
            time.sleep(1) # Делаем паузу между запросами, чтобы не перегружать сервер
            
        except Exception as e:
            print(f"Ошибка при обработке страницы {page}: {e}")
            break

    print(f"\nСбор завершен. Найдено записей за 2024 год: {len(all_records)}")
    
    if not all_records:
        print("Нет данных для анализа. Проверьте HTML-селекторы или URL.")
        return

    # Анализ данных с помощью pandas
    df = pd.DataFrame(all_records)
    
    print("\n--- Топ-10 марок сварочного оборудования ---")
    equip_stats = df['equipment_brand'].value_counts()
    print(equip_stats.head(10))

    print("\n--- Топ-10 типов ОПО ---")
    opo_stats = df['opo_type'].value_counts()
    print(opo_stats.head(10))

if __name__ == "__main__":
    main()
