import feedparser
import json
import os
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# 创建输出目录
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

# 新增：获取单篇论文的编号、类型、完整作者
def get_full_paper_info(arxiv_id):
    url = f"https://arxiv.org/abs/{arxiv_id}"
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        # 1. 完整 arXiv 编号（带版本号）
        full_id_tag = soup.find("div", class_="paper-id")
        full_id = full_id_tag.text.strip() if full_id_tag else f"arXiv:{arxiv_id}"

        # 2. 识别 Announce Type
        announce_type = "new"
        if soup.find("div", class_="announce-cross"):
            announce_type = "cross"
        if soup.find("div", class_="announce-replace"):
            announce_type = "replace"

        # 3. 完整作者列表
        authors_div = soup.find("div", class_="authors")
        authors = []
        if authors_div:
            for a in authors_div.find_all("a"):
                authors.append(a.text.strip())
        authors_str = ", ".join(authors) if authors else "Unknown"

        return full_id, announce_type, authors_str
    except:
        return f"arXiv:{arxiv_id}", "new", ""

# 获取网页原始日期
arxiv_date = get_arxiv_original_date("hep-ex")
print(f"📅 网页原始日期：{arxiv_date}")

# ============== 保留原有的 24小时论文抓取逻辑 ==============
now = datetime.utcnow()
one_day_ago = now - timedelta(hours=24)
CATEGORIES = ["hep-ex", "hep-ph"]

result = {
    "date": arxiv_date,
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
                # 提取 arXiv ID
                arxiv_id = entry.id.split("/")[-1]
                # 调用函数获取完整信息
                full_id, announce_type, full_authors = get_full_paper_info(arxiv_id)

                # 保留原有字段，只修改 author 和 summary
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                pub_time_str = entry.get("published", "")

                # 修复作者字段：用完整作者列表
                author = full_authors if full_authors else entry.get("author", "")

                # 修复 summary 字段：按你的格式
                summary_raw = entry.get("summary", "").strip()
                summary = f"{full_id} Announce Type: {announce_type}\n{summary_raw}"

                papers.append({
                    "title": title,
                    "author": author,
                    "link": link,
                    "time": pub_time_str,
                    "category": cat,
                    "summary": summary
                })
        except Exception as e:
            print(f"⚠️ 处理论文出错: {e}")
            continue

    result[cat] = papers
    print(f"✅ {cat} 抓到：{len(papers)} 篇")

# ============== 完全保留原有的写入逻辑 ==============
with open("output/data.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

os.utime("output/data.json", None)
print("\n🎉 抓取完成！文件已覆盖！")
