import feedparser
import json
import os
import requests

# 创建输出目录
os.makedirs("output", exist_ok=True)

# 监控的 arXiv 分类：实验 + 唯象
CATEGORIES = ["hep-ex", "hep-ph"]
result = {}

for cat in CATEGORIES:
    # 使用 arXiv API 抓取（比RSS更实时）
    url = f"http://export.arxiv.org/api/query?search_query=cat:{cat}&sortBy=submittedDate&sortOrder=descending&max_results=100"
    response = requests.get(url, timeout=10)
    feed = feedparser.parse(response.content)
    papers = []
    for entry in feed.entries:
        papers.append({
            "title": entry.get("title", ""),
            "author": entry.get("author", ""),
            "link": entry.get("link", ""),
            "time": entry.get("published", ""),
            "category": cat,
            "summary": entry.get("summary", "").strip()
        })
    result[cat] = papers

# 生成 JSON 文件
with open("output/data.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"✅ API 抓取完成！")
print(f"hep-ex: {len(result.get('hep-ex', []))} 篇")
print(f"hep-ph: {len(result.get('hep-ph', []))} 篇")
