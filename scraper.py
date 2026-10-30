import csv
import queue
import time
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

# 設定
START_URL = "https://www.musashino-u.ac.jp/"  # 武蔵野大学トップページ
DOMAIN = urlparse(START_URL).netloc
SLEEP_TIME = 0.001  # サーバー負荷軽減用の待機時間（秒）※適度な値を推奨

visited_urls = set()
sitemap_dict = {}

# 巡回待ちURLを管理するキュー（幅優先探索）
url_queue = queue.Queue()
url_queue.put(START_URL)

# 静的ファイル等の除外拡張子
ignore_extensions = (
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".css",
    ".js",
    ".zip",
    ".mp4",
    ".mp3",
    ".ico",
)


def is_valid_url(url):
    """同一ドメインかつHTMLページかどうかを判定"""
    parsed = urlparse(url)
    if parsed.netloc != DOMAIN:
        return False
    if parsed.path.lower().endswith(ignore_extensions):
        return False
    return True


print("--- クローリング開始（無制限） ---")
count = 0  # 保存件数のカウンター

# キューにURLがある限り上限なく処理を継続
while not url_queue.empty():
    url = url_queue.get()

    if url in visited_urls:
        continue

    visited_urls.add(url)

    # アクセス前の負荷軽減待機
    time.sleep(SLEEP_TIME)

    try:
        response = requests.get(
            url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10
        )
        if response.status_code != 200:
            continue

        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")

        # <title>タグの取得
        title_text = soup.title.string.strip() if soup.title else "No Title"
        sitemap_dict[url] = title_text

        # カウントを増やして何件目かを表示
        count += 1
        print(f"[{count}件目] {url} - {title_text}")

        # ページ内のリンクを取得してキューに追加
        for a_tag in soup.find_all("a", href=True):
            next_url = urljoin(url, a_tag["href"]).split("#")[0]

            if is_valid_url(next_url) and next_url not in visited_urls:
                url_queue.put(next_url)

    except Exception as e:
        print(f"Error crawling {url}: {e}")

# CSVへ出力
csv_filename = "sitemap.csv"
with open(csv_filename, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["No.", "URL", "Title"])
    for idx, (url, title) in enumerate(sitemap_dict.items(), 1):
        writer.writerow([idx, url, title])

print(f"\n完了: 合計 {len(sitemap_dict)} 件のページを {csv_filename} に保存しました。")