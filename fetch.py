import feedparser
import json
import os
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# 创建输出目录
os.makedirs("output", exist_ok=True)

# ============== 从网页抓取【原始日期格式】 ==============
def get_arxiv_original_date(category="hep-ex"):
    url = f"https://arxiv.org/list/{category}/new"
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        h3 = soup.find("h3", string=lambda t: t and "Showing new listings for" in t)
        if h3:
            return h3.text.replace("Showing new listings for ", "").strip()
    except:
        pass
    return "No date"

# 获取网页原始日期（例如：Friday, 17 April 2026）
arxiv_date = get_arxiv_original_date("hep-ex")
print(f"📅 网页原始日期：{arxiv_date}")

# ============== 抓取最近24小时论文 ==============
now = datetime.utcnow()
one_day_ago = now - timedelta(hours=24)
CATEGORIES = ["hep-ex", "hep-ph"]

result = {
    "date": arxiv_date,  # 直接保存网页原始格式
    "hep-ex": [],
    "hep-ph": []
}

for cat in CATEGORIES:
    url = f"http://export.arxiv.org/api/query?search_query=cat:{cat}&sortBy=submittedDate&sortOrder=descending&max_results=100"
    feed = feedparser.parse(url)

    papers = []
    for entry in feed.entries:
        try:
            pub_time = datetime(*entry.published_parsed[:6])
            if pub_time >= one_day_ago:
                papers.append({
                    "title": entry.get("title", "").strip(),
                    "author": entry.get("author", ""),
                    "link": entry.get("link", ""),
                    "time": entry.get("published", ""),
                    "category": cat,
                    "summary": entry.get("summary", "").strip()
                })
        except:
            continue

    result[cat] = papers
    print(f"✅ {cat} 抓到：{len(papers)} 篇")

# ============== 覆盖写入文件 ==============
with open("output/data.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

os.utime("output/data.json", None)
print("\n🎉 抓取完成！文件已覆盖！")
