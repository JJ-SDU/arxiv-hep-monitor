import feedparser
import json
import os
import filecmp

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
            "category": cat,
            "summary": entry.get("summary", "").strip()
        })
    result[cat] = papers

# 调试：先读取旧文件（如果存在）
old_data = None
if os.path.exists("output/data.json"):
    with open("output/data.json", "r", encoding="utf-8") as f:
        old_data = json.load(f)

# 生成 JSON 文件
with open("output/data.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

# 调试：对比新旧数据
new_data = result
if old_data:
    if old_data == new_data:
        print("⚠️  抓取完成，但数据和旧文件完全一致，无更新！")
    else:
        print("✅ 抓取完成！数据有更新！")
else:
    print("✅ 抓取完成！首次生成文件！")

print(f"hep-ex 抓取了 {len(result.get('hep-ex', []))} 篇")
print(f"hep-ph 抓取了 {len(result.get('hep-ph', []))} 篇")
