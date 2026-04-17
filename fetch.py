import feedparser
import json
import os
from datetime import datetime, timedelta

# 创建输出目录
os.makedirs("output", exist_ok=True)

# ============== 抓取最近24小时论文（解决时区+空数据问题）==============
now = datetime.utcnow()
one_day_ago = now - timedelta(hours=24)

CATEGORIES = ["hep-ex", "hep-ph"]
result = {
    "listing_title": "",  # 这里存你要的文字：Showing new listings for ...
    "papers": {}
}

for cat in CATEGORIES:
    url = f"http://export.arxiv.org/api/query?search_query=cat:{cat}&sortBy=submittedDate&sortOrder=descending&max_results=100"
    feed = feedparser.parse(url)

    # ========== 抓取你要的文字：Showing new listings for XXX ==========
    if feed.feed.get("title", ""):
        result["listing_title"] = feed.feed.title

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

    result["papers"][cat] = papers
    print(f"✅ {cat} 抓到：{len(papers)} 篇")

print(f"📝 抓取到标题：{result['listing_title']}")

# ============== 强制覆盖写入 ==============
with open("output/data.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

# 强制修改时间戳 → Git 必提交
os.utime("output/data.json", None)

print("\n🎉 全部完成！文件已覆盖！")
