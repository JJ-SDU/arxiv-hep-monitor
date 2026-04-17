import feedparser
import json
import os
from datetime import datetime

# 创建输出目录
os.makedirs("output", exist_ok=True)

# 获取今天的日期（arXiv 日期格式：Thu, 27 Mar 2025）
today = datetime.utcnow().strftime("%a, %d %b %Y")

# 监控分类
CATEGORIES = ["hep-ex", "hep-ph"]
result = {}

print(f"📅 只抓取今天的论文：{today}")

for cat in CATEGORIES:
    url = f"http://export.arxiv.org/api/query?search_query=cat:{cat}&sortBy=submittedDate&sortOrder=descending&max_results=100"
    feed = feedparser.parse(url)
    
    papers = []
    for entry in feed.entries:
        pub_date = entry.get("published", "")
        
        # ✅ 只保留【今天发布】的论文
        if today in pub_date:
            papers.append({
                "title": entry.get("title", "").strip(),
                "author": entry.get("author", ""),
                "link": entry.get("link", ""),
                "time": entry.get("published", ""),
                "category": cat,
                "summary": entry.get("summary", "").strip()
            })

    result[cat] = papers
    print(f"✅ {cat} 今天抓取到：{len(papers)} 篇")

# ✅ 强制覆盖写入 data.json（完全替换旧文件）
with open("output/data.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("\n🎉 完成！只保留今天论文，旧文件已覆盖")
