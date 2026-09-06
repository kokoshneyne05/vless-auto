import requests
import re
import socket
import time
import concurrent.futures

# Сюда мы добавим ваши ссылки на подписки и конфиги позже
SOURCES = [
  https://github.com/kort0881/vpn-vless-configs-russia/raw/refs/heads/main/output/vless.txt
]

def get_nodes(url):
    try:
        response = requests.get(url, timeout=10)
        # Ищем все строки, начинающиеся с vless://
        return re.findall(r'vless://\S+', response.text)
    except Exception as e:
        print(f"Ошибка чтения {url}: {e}")
        return []

def test_node(link):
    # Извлекаем IP/домен и порт из ссылки vless://uuid@host:port?...
    match = re.search(r'vless://[^@]+@([^:]+):(\d+)', link)
    if not match:
        return None
    
    host, port = match.group(1), int(match.group(2))
    
    try:
        start_time = time.time()
        # Пробуем установить TCP-соединение с сервером (таймаут 3 секунды)
        with socket.create_connection((host, port), timeout=3):
            ping = (time.time() - start_time) * 1000
        return {'link': link, 'ping': ping}
    except Exception:
        return None # Сервер недоступен

def main():
    all_links = set()
    print("Собираем узлы...")
    for source in SOURCES:
        all_links.update(get_nodes(source))
    
    print(f"Собрано уникальных узлов: {len(all_links)}")
    
    results = []
    print("Начинаем тестирование...")
    # Тестируем в 20 потоков для скорости
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(test_node, link): link for link in all_links}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                results.append(res)

    # Сортируем по пингу (от меньшего к большему) и берем топ-20
    top_20 = sorted(results, key=lambda x: x['ping'])[:20]
    
    print(f"Рабочих узлов найдено: {len(results)}. Отбираем топ-20.")
    
    # Записываем результат в файл подписки
    with open('sub.txt', 'w', encoding='utf-8') as f:
        for node in top_20:
            f.write(node['link'] + '\n')
            
    print("Файл sub.txt успешно сгенерирован.")

if __name__ == "__main__":
    main()
