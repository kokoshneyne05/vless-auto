import urllib.request
import re
import os
import json
import gzip
import shutil
import subprocess
import glob

SOURCES = [
    "https://github.com/kort0881/vpn-vless-configs-russia/raw/refs/heads/main/output/vless.txt"
]

def get_nodes(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8')
            
            content = content.replace("&amp;", "&")
            
            links = []
            for line in content.splitlines():
                match = re.search(r'(vless://\S+)', line)
                if match:
                    clean_link = match.group(1).split('|')[0].strip()
                    links.append(clean_link)
            return links
    except Exception as e:
        print(f"Ошибка чтения {url}: {e}")
        return []

def main():
    all_links = set()
    for s in SOURCES:
        all_links.update(get_nodes(s))
    
    if not all_links:
        print("Не найдено ни одной ссылки. Завершение работы.")
        return
        
    with open('raw_nodes.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(all_links))
        
    print(f"Собрано {len(all_links)} узлов. Загрузка ядра и баз данных...")
    
    # 1. Скачиваем LiteSpeedTest
    bin_url = "https://github.com/xxf098/LiteSpeedTest/releases/download/v0.15.0/lite-linux-amd64-v0.15.0.gz"
    req = urllib.request.Request(bin_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as r, open('lite.gz', 'wb') as out:
        out.write(r.read())
        
    with gzip.open('lite.gz', 'rb') as f_in, open('lite', 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
    os.chmod('lite', 0o755)

    # 2. Скачиваем geoip.dat и geosite.dat (обязательны для работы Xray-core)
    try:
        urllib.request.urlretrieve("https://github.com/v2fly/geoip/releases/latest/download/geoip.dat", "geoip.dat")
        urllib.request.urlretrieve("https://github.com/v2fly/domain-list-community/releases/latest/download/dlc.dat", "geosite.dat")
    except Exception as e:
        print("Не удалось скачать geo-файлы, продолжаем без них...", e)

    # 3. Настраиваем идеальный пинг (204 No Content)
    config = {
        "outputMode": 4,             
        "speedtestMode": "pingonly", 
        "pingMethod": "httpping",  
        "pingAddress": "http://cp.cloudflare.com/generate_204", 
        "concurrency": 20            
    }
    with open('config.json', 'w') as f:
        json.dump(config, f)

    print("Начинаем реальный прозвон серверов...")
    subprocess.run(["./lite", "--config", "config.json", "--test", "raw_nodes.txt"])

    txt_files = [f for f in glob.glob("*.txt") if f not in ("raw_nodes.txt", "sub.txt")]
    if not txt_files:
        print("Ошибка: Ни один сервер не прошел проверку или тест упал!")
        return

    latest_file = max(txt_files, key=os.path.getctime)
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        working_nodes = [line.strip() for line in f if line.strip().startswith('vless://')]
    
    print(f"Прошли реальную проверку: {len(working_nodes)}")
    
    if not working_nodes:
         print("Нет рабочих узлов. Файл sub.txt не обновлен.")
         return
         
    top_20 = working_nodes[:20]
    
    with open('sub.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(top_20))
        
    print("Файл sub.txt успешно обновлен!")

if __name__ == "__main__":
    main()
