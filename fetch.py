import feedparser
import json
import os
from datetime import datetime, timedelta

# 输出目录
os.makedirs("output", exist_ok=True)

# ===================== 核心修复：抓取最近 24 小时内的论文（无视时区）=====================
now = datetime.utcnow()
one_day_ago = now - timedelta(hours=24)  # 最近 24 小时
print(f"🕒 抓取最近 24 小时内的论文（UTC）: {one_day_ago.strftime('%Y-%m-%d %H:%M')} ~ {now.strftime('%Y-%m-%d %H:%M')}")

# 分类
CATEGORIES = ["hep-ex", "hep-ph"]
result = {}

for cat in CATEGORIES:
    url = f"http://export.arxiv.org/api/query?search_query=cat:{cat}&sortBy=submittedDate&sortOrder=descending&max_results=100"
    feed = feedparser.parse(url)

    papers = []
    for entry in feed.entries:
        try:
            # 解析论文发布时间
            pub_time = datetime(*entry.published_parsed[:6])

            # 只保留【最近 24 小时内】的论文
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
    print(f"✅ {cat} 抓到：{len(papers)} 篇")

# ===================== 强制覆盖写入（旧文件直接没了）=====================
with open("output/data.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

# 强制修改时间戳 → 确保 Git 一定提交
os.utime("output/data.json", None)

print("\n🎉 抓取完成！文件已强制覆盖！")
