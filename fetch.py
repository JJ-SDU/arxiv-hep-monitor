import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

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

# ============== 从 list/new 页面抓取全部论文（含new/cross/replace）==============
def fetch_from_list_page(category):
    url = f"https://arxiv.org/list/{category}/new"
    try:
        response = requests.get(url, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
    except:
        return []

    papers = []
    dts = soup.find_all("dt")

    for dt in dts:
        # 1. arXiv 编号
        id_a = dt.find("a", title="Abstract")
        if not id_a:
            continue
        arxiv_id = id_a["href"].split("/")[-1]
        full_arxiv_id = f"arXiv:{arxiv_id}"

        # 2. 识别 type：默认 new，cross-list → cross，replaced → replace
        type_text = "new"  # 默认值
        if "cross-list from" in dt.text:
            type_text = "cross"
        elif "replaced" in dt.text:
            type_text = "replace"

        # 3. 对应详情 dd
        dd = dt.find_next_sibling("dd")
        if not dd:
            continue

        # 4. 完整作者（包含括号及文字）
        authors = []
        author_div = dd.find("div", class_="list-authors")
        if author_div:
            # 直接获取整个作者行的完整文本
            author_text = author_div.get_text(strip=True).replace("Authors:", "").strip()
            # 按逗号分割保留全部内容
            authors = [a.strip() for a in author_text.split(",")]
        author_str = ", ".join(authors) if authors else "Unknown"

        # 5. 标题
        title_div = dd.find("div", class_="list-title mathjax")
        title = title_div.text.replace("Title:", "").strip() if title_div else ""

        # 6. 链接
        link = f"https://arxiv.org/abs/{arxiv_id}"

        # 7. 抓取摘要（从列表页正文直接抓，字段名改为 abstract）
        abstract_p = dd.find("p", class_="mathjax")
        abstract = abstract_p.get_text(strip=True) if abstract_p else ""

        papers.append({
            "title": title,
            "author": author_str,
            "link": link,
            "abstract": abstract,
            "type": type_text
        })

    return papers

# ============== 新增 hep-lat 和 hep-th 分类 ==============
CATEGORIES = ["hep-ex", "hep-ph", "hep-lat", "hep-th"]

result = {
    "date": arxiv_date,
    "hep-ex": [],
    "hep-ph": [],
    "hep-lat": [],
    "hep-th": []
}

for cat in CATEGORIES:
    papers = fetch_from_list_page(cat)
    result[cat] = papers
    print(f"✅ {cat} 抓到：{len(papers)} 篇")

# ============== 写入原路径 ==============
with open("output/data.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

os.utime("output/data.json", None)
print("\n🎉 抓取完成！文件已覆盖！")
