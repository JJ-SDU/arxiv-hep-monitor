import feedparser
import json
import os
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# 创建输出目录（保留原功能）
os.makedirs("output", exist_ok=True)

# ============== 从网页抓取【原始日期格式】（保留原功能）==============
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

# ============== 核心修复：从网页抓取完整论文（含编号、类型、全作者）==============
def fetch_arxiv_web(category):
    url = f"https://arxiv.org/list/{category}/new"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    
    papers = []
    for dt in soup.find_all("dt"):
        # 1. 提取 arXiv 编号（带版本）
        id_span = dt.find("span", class_="list-identifier")
        if not id_span:
            continue
        arxiv_id = id_span.text.strip().split()[0]

        # 2. 自动识别类型：new / cross-list / replacement
        announce_type = "new"
        if "cross-list" in dt.text:
            announce_type = "cross-list"
        elif "replacement" in dt.text:
            announce_type = "replacement"

        # 3. 取下一条 dd 信息
        dd = dt.find_next_sibling("dd")
        if not dd:
            continue

        # 4. 抓取完整作者（修复：不再只抓一个）
        authors = []
        author_div = dd.find("div", class_="list-authors")
        if author_div:
            for a in author_div.find_all("a"):
                authors.append(a.text.strip())
        author_str = ", ".join(authors) if authors else "Unknown"

        # 5. 标题
        title = dd.find("div", class_="list-title").text.replace("Title:", "").strip()

        # 6. 链接
        link = "https://arxiv.org/abs/" + arxiv_id.split(":")[1]

        # 7. 摘要（修复：前面加上编号 + Announce Type）
        abstract_p = dd.find("p", class_="list-abstract")
        abstract_raw = abstract_p.text.replace("Abstract:", "").strip() if abstract_p else ""
        summary = f"{arxiv_id} Announce Type: {announce_type}\n{abstract_raw}"

        # 8. 时间（用网页日期保持统一）
        pub_time = arxiv_date

        # 组装成和原来一样的结构，不破坏输出格式
        papers.append({
            "title": title,
            "author": author_str,
            "link": link,
            "time": pub_time,
            "category": category,
            "summary": summary
        })
    return papers

# ============== 保留原来的结构与输出格式 ==============
now = datetime.utcnow()
one_day_ago = now - timedelta(hours=24)
CATEGORIES = ["hep-ex", "hep-ph"]

result = {
    "date": arxiv_date,
    "hep-ex": [],
    "hep-ph": []
}

# 改用网页抓取，保证作者完整、带编号、带类型
for cat in CATEGORIES:
    papers = fetch_arxiv_web(cat)
    result[cat] = papers
    print(f"✅ {cat} 抓到：{len(papers)} 篇")

# ============== 覆盖写入文件（完全不变）==============
with open("output/data.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

os.utime("output/data.json", None)
print("\n🎉 抓取完成！文件已覆盖！")
