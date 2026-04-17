import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 创建输出目录
os.makedirs("output", exist_ok=True)

# ============== 获取网页日期 ==============
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

# ============== 抓取一个 list/new 页面全部文章 ==============
def fetch_all_from_list(category):
    url = f"https://arxiv.org/list/{category}/new"
    try:
        response = requests.get(url, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
    except:
        return []

    papers = []
    dts = soup.find_all("dt")

    for dt in dts:
        # 获取 arXiv 编号
        id_a = dt.find("a", title="Abstract")
        if not id_a:
            continue
        arxiv_id = id_a["href"].split("/")[-1]

        # 获取对应 dd 内容
        dd = dt.find_next_sibling("dd")
        if not dd:
            continue

        # 完整作者
        authors = []
        author_div = dd.find("div", class_="list-authors")
        if author_div:
            for a in author_div.find_all("a"):
                authors.append(a.text.strip())
        author_str = ", ".join(authors) if authors else "Unknown"

        # 标题
        title_div = dd.find("div", class_="list-title")
        title = title_div.text.replace("Title:", "").strip() if title_div else ""

        # 链接
        link = f"https://arxiv.org/abs/{arxiv_id}"

        # 摘要（只保留摘要）
        abstract_p = dd.find("p", class_="list-abstract")
        summary = abstract_p.text.replace("Abstract:", "").strip() if abstract_p else ""

        # 时间
        pub_time = get_arxiv_original_date(category)

        # 加入列表
        papers.append({
            "title": title,
            "author": author_str,
            "link": link,
            "time": pub_time,
            "category": category,
            "summary": summary
        })

    return papers

# ============== 主程序 ==============
CATEGORIES = ["hep-ex", "hep-ph"]
arxiv_date = get_arxiv_original_date("hep-ex")

result = {
    "date": arxiv_date,
    "hep-ex": [],
    "hep-ph": []
}

for cat in CATEGORIES:
    papers = fetch_all_from_list(cat)
    result[cat] = papers
    print(f"✅ {cat} 抓取完成：{len(papers)} 篇")

# ============== 输出文件 ==============
with open("output/data.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

os.utime("output/data.json", None)
print("\n🎉 全部抓取完成！")
