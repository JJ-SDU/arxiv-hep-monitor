import feedparser
import json
import os
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# 创建输出目录
os.makedirs("output", exist_ok=True)

# ============== 从网页抓取【原始日期格式】 ==============
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

# 新增：从网页获取一篇论文的 arXiv编号、AnnounceType、完整作者
def get_paper_detail(arxiv_id):
    url = f"https://arxiv.org/abs/{arxiv_id}"
    try:
        res = requests.get(url, timeout=8)
        soup = BeautifulSoup(res.text, "html.parser")
        
        # 获取完整编号带版本
        title_id = soup.find("h1", class_="title")
        full_id = f"arXiv:{arxiv_id}"
        if title_id and title_id.next_sibling:
            full_id = title_id.next_sibling.text.strip()
        
        # 获取 announce type
        announce_type = "new"
        if soup.find("div", string=lambda s: s and "cross-list" in str(s)):
            announce_type = "cross-list"
        if soup.find("div", string=lambda s: s and "replacement" in str(s)):
            announce_type = "replacement"
        
        # 获取完整作者
        authors = []
        auth_div = soup.find("div", class_="authors")
        if auth_div:
            for a in auth_div.find_all("a"):
                authors.append(a.text.strip())
        author_str = ", ".join(authors) if authors else ""
        
        return full_id, announce_type, author_str
    except:
        return f"arXiv:{arxiv_id}", "new", ""

# 获取网页原始日期（例如：Friday, 17 April 2026）
arxiv_date = get_arxiv_original_date("hep-ex")
print(f"📅 网页原始日期：{arxiv_date}")

# ============== 抓取最近24小时论文 ==============
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
                # 提取 arXiv 编号
                arxiv_id = entry.id.split("/")[-1]
                full_id, announce_type, full_authors = get_paper_detail(arxiv_id)
                
                # 原来的字段
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                pub_time_str = entry.get("published", "")
                
                # 修复作者
                author = full_authors if full_authors else entry.get("author", "")
                
                # 修复摘要：前面加上编号 + Announce Type
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
            continue

    result[cat] = papers
    print(f"✅ {cat} 抓到：{len(papers)} 篇")

# ============== 覆盖写入文件 ==============
with open("output/data.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

os.utime("output/data.json", None)
print("\n🎉 抓取完成！文件已覆盖！")
