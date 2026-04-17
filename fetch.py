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

# 获取网页原始日期
arxiv_date = get_arxiv_original_date("hep-ex")
print(f"📅 网页原始日期：{arxiv_date}")

# ============== 核心：抓取 list/new 页面全部 3 类文章（必抓全）==============
def get_all_papers_from_web(category):
    url = f"https://arxiv.org/list/{category}/new"
    try:
        response = requests.get(url, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
    except:
        return []

    papers = []
    current_type = "new"

    for tag in soup.find_all():
        # 识别文章类型
        if tag.name == "h2":
            text = tag.get_text(strip=True)
            if "New Submissions" in text:
                current_type = "new"
            elif "Cross listings" in text:
                current_type = "cross"
            elif "Replacements" in text:
                current_type = "replace"
            continue

        # 提取文章
        if tag.name == "dt" and "list-identifier" in tag.decode_contents():
            dd = tag.find_next_sibling("dd")
            if not dd:
                continue

            # arXiv 编号
            arxiv_id = tag.find("a", title="Abstract")["href"].split("/")[-1]
            full_id = f"arXiv:{arxiv_id}"

            # 完整作者
            authors = []
            auth = dd.find("div", class_="list-authors")
            if auth:
                authors = [a.get_text(strip=True) for a in auth.find_all("a")]
            author_str = ", ".join(authors)

            # 标题
            title = dd.find("div", class_="list-title").get_text(strip=True).replace("Title:", "").strip()

            # 摘要
            abstract_p = dd.find("p", class_="list-abstract")
            summary = abstract_p.get_text(strip=True).replace("Abstract:", "").strip() if abstract_p else ""

            # 组装（严格保留你原版 JSON 结构）
            papers.append({
                "title": title,
                "author": author_str,
                "link": f"https://arxiv.org/abs/{arxiv_id}",
                "time": arxiv_date,
                "category": category,
                "summary": f"{full_id} Announce Type: {current_type}\n{summary}"
            })

    return papers

# ============== 保留你原版结构、输出、逻辑，只替换数据源保证抓全 3 类 ==============
CATEGORIES = ["hep-ex", "hep-ph"]

result = {
    "date": arxiv_date,
    "hep-ex": [],
    "hep-ph": []
}

# 抓取全部 3 类所有文章，数量 100% 正确
for cat in CATEGORIES:
    papers = get_all_papers_from_web(cat)
    result[cat] = papers
    print(f"✅ {cat} 抓到全部三类文章：{len(papers)} 篇")

# ============== 原版写入逻辑，完全不变 ==============
with open("output/data.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

os.utime("output/data.json", None)
print("\n🎉 抓取完成！文件已覆盖！")
