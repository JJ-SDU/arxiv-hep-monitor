import feedparser
import json
import os

# 创建输出目录
os.makedirs("output", exist_ok=True)

# 监控的 arXiv 分类：hep-th（理论）、hep-ex（实验）
CATEGORIES = {
    "hep-th": "https://arxiv.org/rss/hep-th",
    "hep-ex": "https://arxiv.org/rss/hep-ex"
}

result = {}

# 抓取每个分类的最新30篇论文
for cat, url in CATEGORIES.items():
    feed = feedparser.parse(url)
    papers = []
    for entry in feed.entries[:30]:
        papers.append({
            "title": entry.get("title", ""),
            "author": entry.get("author", ""),
            "link": entry.get("link", ""),
            "time": entry.get("published", ""),
            "category": cat
        })
    result[cat] = papers

# 生成 JSON 文件，供小程序调用
with open("output/data.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("✅ 抓取完成，output/data.json 已生成")
