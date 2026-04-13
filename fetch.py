import feedparser
import json
import os

# 创建输出目录
os.makedirs("output", exist_ok=True)

# 监控的 arXiv 分类：实验 + 唯象
CATEGORIES = {
    "hep-ex": "https://arxiv.org/rss/hep-ex",
    "hep-ph": "https://arxiv.org/rss/hep-ph"
}

result = {}

# 抓取每个分类的最新 100 篇（有多少抓多少）
for cat, url in CATEGORIES.items():
    feed = feedparser.parse(url)
    papers = []
    # 最多取 100 篇，不写死 30 篇
    for entry in feed.entries[:100]:
        papers.append({
            "title": entry.get("title", ""),
            "author": entry.get("author", ""),
            "link": entry.get("link", ""),
            "time": entry.get("published", ""),
            "category": cat
        })
    result[cat] = papers

# 生成 JSON 文件
with open("output/data.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("✅ 抓取完成！实验 + 唯象，最多 100 篇")
