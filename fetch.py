import feedparser
import json
import os
from datetime import datetime, timedelta

# 输出目录
os.makedirs("output", exist_ok=True)

# 抓取最近24小时论文
now = datetime.utcnow()
one_day_ago = now - timedelta(hours=24)

CATEGORIES = ["hep-ex", "hep-ph"]
result = {
    "date": "",  # 只存：Friday, 17 April 2026
    "hep-ex": [],
    "hep-ph": []
}

# 抓取 arXiv 标题日期
for cat in CATEGORIES:
    url = f"http://export.arxiv.org/api/query?search_query=cat:{cat}&sortBy=submittedDate&sortOrder=descending&max_results=100"
    feed = feedparser.parse(url)

    # 提取干净日期（关键！）
    title = feed.feed.get("title", "")
    if "Showing new listings for" in title:
        raw_date = title.replace("Showing new listings for ", "").strip()
        result["date"] = raw_date

    # 只抓最近24小时
    papers = []
    for entry in feed.entries:
        try:
            pub_time = datetime(*entry.published_parsed[:6])
            if pub_time >= one_day_ago:
                papers.append({
                    "title": entry.title.strip(),
                    "author": entry.author,
                    "link": entry.link,
                    "time": entry.published,
                    "category": cat,
                    "summary": entry.summary.strip()
                })
        except:
            continue

    result[cat] = papers

# 强制覆盖写入
with open("output/data.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

os.utime("output/data.json", None)
print("✅ 抓取完成！日期：", result["date"])
