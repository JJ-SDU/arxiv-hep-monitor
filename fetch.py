import json
import os
import requests
from bs4 import BeautifulSoup

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

# ============== 抓取一个 list/new 页面全部文章（修复版）==============
def fetch_all_from_list(category):
    url = f"https://arxiv.org/list/{category}/new"
    try:
        response = requests.get(url, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
    except:
        return []

    papers = []
    # 直接按顺序抓取所有 dt/dd 对，避免按h2识别导致的问题
    dts = soup.find_all("dt")
    dds = soup.find_all("dd")

    for i, dt in enumerate(dts):
        if i >= len(dds):
            continue
        dd = dds[i]

        # 1. 提取 arXiv 完整编号（例如 arXiv:2604.15049）
        id_span = dt.find("span", class_="list-identifier")
        if not id_span:
            continue
        arxiv_number = id_span.find("a").get_text(strip=True)

        # 2. 提取括号里的 announce type 原文（例如 cross-list from astro-ph.HE）
        announce_type = ""
        sup_text = id_span.find("sup")
        if sup_text:
            announce_type = sup_text.get_text(strip=True).strip("()")

        # 3. 完整作者列表（含括号内的合作组说明）
        author_str = ""
        auth_div = dd.find("div", class_="list-authors")
        if auth_div:
            # 直接取整个div的文本，不只是<a>标签，这样能包含括号内容
            author_str = auth_div.get_text(strip=True).replace("Authors:", "").strip()

        # 4. 标题
        title = ""
        title_div = dd.find("div", class_="list-title")
        if title_div:
            title = title_div.get_text(strip=True).replace("Title:", "").strip()

        # 5. 链接
        link = f"https://arxiv.org/abs/{arxiv_number.replace('arXiv:', '')}"

        # 6. 摘要（修复空摘要问题，直接取完整文本）
        summary = ""
        abs_p = dd.find("p", class_="list-abstract")
        if abs_p:
            summary = abs_p.get_text(strip=True).replace("Abstract:", "").strip()

        # 7. 最终字段：按你要求的结构
        papers.append({
            "title": title,
            "author": author_str,
            "link": link,
            "arXiv number": arxiv_number,
            "Announce type": announce_type,
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
