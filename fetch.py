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

    # 先定位三个分段标题，确定每篇属于哪一类
    h2_new = soup.find("h2", string=lambda s: s and "New Submissions" in s)
    h2_cross = soup.find("h2", string=lambda s: s and "Cross listings" in s)
    h2_replace = soup.find("h2", string=lambda s: s and "Replacements" in s)

    # 遍历所有论文 dt
    dts = soup.find_all("dt")
    for dt in dts:
        # 1. 提取 arXiv 完整编号
        id_span = dt.find("span", class_="list-identifier")
        if not id_span:
            continue
        arxiv_id = id_span.text.strip().split()[0]  # 形如 arXiv:2501.13530

        # 2. 判断属于哪一类
        announce_type = "new"
        if h2_cross and dt.find_previous("h2") == h2_cross:
            announce_type = "cross"
        elif h2_replace and dt.find_previous("h2") == h2_replace:
            announce_type = "replace"

        # 3. 取下一条详情 dd
        dd = dt.find_next_sibling("dd")
        if not dd:
            continue

        # 4. 完整作者
        authors = []
        author_div = dd.find("div", class_="list-authors")
        if author_div:
            for a in author_div.find_all("a"):
                authors.append(a.text.strip())
        author_str = ", ".join(authors) if authors else "Unknown"

        # 5. 标题
        title_div = dd.find("div", class_="list-title")
        title = title_div.text.replace("Title:", "").strip() if title_div else ""

        # 6. 链接
        link = f"https://arxiv.org/abs/{arxiv_id.split(':')[-1]}"

        # 7. 摘要（严格按你要的格式）
        abstract_p = dd.find("p", class_="list-abstract")
        abstract_raw = abstract_p.text.replace("Abstract:", "").strip() if abstract_p else ""
        summary = f"{arxiv_id} Announce Type: {announce_type}\n{abstract_raw}"

        papers.append({
            "title": title,
            "author": author_str,
            "link": link,
            "time": arxiv_date,
            "category": category,
            "summary": summary
        })

    return papers

# ============== 抓取 hep-ex + hep-ph 全部三类 ==============
CATEGORIES = ["hep-ex", "hep-ph"]

result = {
    "date": arxiv_date,
    "hep-ex": [],
    "hep-ph": []
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
