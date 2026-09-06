import urllib.request
import re
import os
import json
import gzip
import shutil
import subprocess
import glob

# Вставьте ваши ссылки сюда
SOURCES = [
https://github.com/kort0881/vpn-vless-configs-russia/raw/refs/heads/main/output/vless.txt
]

def get_nodes(url):
    try:
        # Притворяемся браузером, чтобы источники нас не блокировали
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            text = response.read().decode('utf-8')
        return re.findall(r'vless://\S+', text)
    except Exception as e:
        print(f"Ошибка чтения {url}: {e}")
        return []

def main():
    all_links = set()
    for s in SOURCES:
        all_links.update(get_nodes(s))
    
    with open('raw_nodes.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(all_links))
        
    print(f"Собрано {len(all_links)} узлов. Загрузка ядра LiteSpeedTest...")
    
    # 1. Скачиваем утилиту (она содержит внутри Xray-core)
    bin_url = "https://github.com/xxf098/LiteSpeedTest/releases/download/v0.15.0/lite-linux-amd64-v0.15.0.gz"
    req = urllib.request.Request(bin_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as r, open('lite.gz', 'wb') as out:
        out.write(r.read())
        
    # Распаковываем и даем права на запуск
    with gzip.open('lite.gz', 'rb') as f_in, open('lite', 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
    os.chmod('lite', 0o755)

    # 2. Настраиваем реальный тест
    config = {
        "outputMode": 4,             # Сохранить только рабочие узлы в текстовый файл
        "speedtestMode": "pingonly", # Делаем реальный HTTP-пинг (через прокси). НЕ "all", иначе GitHub забанит за перерасход трафика при скачивании файлов!
        "pingMethod": "googleping",  # Пингуем Google (если ответ 204, значит инет работает)
        "concurrency": 20            # Проверять по 20 серверов одновременно
    }
    with open('config.json', 'w') as f:
        json.dump(config, f)

    print("Начинаем реальный прозвон серверов...")
    # 3. Запускаем тест
    subprocess.run(["./lite", "--config", "config.json", "--test", "raw_nodes.txt"])

    # 4. LiteSpeedTest создает файл с результатами (с датой в названии). Ищем его.
    txt_files = [f for f in glob.glob("*.txt") if f not in ("raw_nodes.txt", "sub.txt")]
    if not txt_files:
        print("Ошибка: Ни один сервер не прошел проверку или тест упал!")
        return

    # Берем самый свежий файл из созданных
    latest_file = max(txt_files, key=os.path.getctime)
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        # Утилита уже отсортировала их от лучших к худшим
        working_nodes = [line.strip() for line in f if line.strip().startswith('vless://')]
    
    print(f"Прошли реальную проверку: {len(working_nodes)}")
    
    # Берем топ-20
    top_20 = working_nodes[:20]
    
    with open('sub.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(top_20))
        
    print("Файл sub.txt успешно обновлен (Топ-20 рабочих серверов)!")

if __name__ == "__main__":
    main()
