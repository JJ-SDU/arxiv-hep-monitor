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

        # 2. 识别类型（仅用于分类，不输出）
        announce_type = "new"
        if "cross-list" in dt.text:
            announce_type = "cross"
        elif "replacement" in dt.text:
            announce_type = "replace"

        # 3. 对应详情 dd
        dd = dt.find_next_sibling("dd")
        if not dd:
            continue

        # 4. 完整作者
        author_str = "Unknown"
        author_div = dd.find("div", class_="list-authors")
        if author_div:
            author_str = author_div.get_text(strip=True).replace("Authors:", "").strip()

        # 5. 标题
        title_div = dd.find("div", class_="list-title")
        title = title_div.text.replace("Title:", "").strip() if title_div else ""

        # 6. 链接 → 已修改为 PDF 链接
        link = f"https://arxiv.org/pdf/{arxiv_id}"

        # 7. 摘要
        abstract_p = dd.find("p", class_="list-abstract")
        summary = abstract_p.text.replace("Abstract:", "").strip() if abstract_p else ""

        # 只保留要求的 5 个字段
        paper = {
            "title": title,
            "author": author_str,
            "link": link,
            "arXiv number": full_arxiv_id,
            "summary": summary
        }

        papers.append((announce_type, paper))

    return papers

# ============== 统一分类函数：new / cross / replace ==============
def categorize_papers(papers):
    categorized = {
        "new": [],
        "cross": [],
        "replace": []
    }
    for announce_type, paper in papers:
        if announce_type == "new":
            categorized["new"].append(paper)
        elif announce_type == "cross":
            categorized["cross"].append(paper)
        elif announce_type == "replace":
            categorized["replace"].append(paper)
    return categorized

# ============== 抓取两个分类 ==============
CATEGORIES = ["hep-ex", "hep-ph"]

result = {
    "date": arxiv_date,
    "hep-ex": [],
    "hep-ph": []
}

for cat in CATEGORIES:
    papers = fetch_from_list_page(cat)
    result[cat] = categorize_papers(papers)
    
    new_cnt = len(result[cat]["new"])
    cross_cnt = len(result[cat]["cross"])
    replace_cnt = len(result[cat]["replace"])
    print(f"✅ {cat} 抓到：new={new_cnt} cross={cross_cnt} replace={replace_cnt} 总计={new_cnt+cross_cnt+replace_cnt}")

# ============== 写入原路径 ==============
with open("output/data.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

os.utime("output/data.json", None)
print("\n🎉 抓取完成！文件已覆盖！")
