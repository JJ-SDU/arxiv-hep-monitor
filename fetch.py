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
    
    # 按章节抓取，严格区分 new / cross / replace
    sections = [
        ("New submissions", "new"),
        ("Cross submissions", "cross"),
        ("Replacement submissions", "replace")
    ]

    for section_title, type_val in sections:
        for h3 in soup.find_all("h3"):
            if section_title in h3.get_text(strip=True):
                # 找到当前章节下的所有论文 dt
                next_node = h3.find_next_sibling()
                while next_node and next_node.name == 'dl':
                    dts = next_node.find_all("dt")
                    for dt in dts:
                        id_a = dt.find("a", title="Abstract")
                        if not id_a:
                            continue
                        arxiv_id = id_a["href"].split("/")[-1]
                        full_arxiv_id = f"arXiv:{arxiv_id}"

                        dd = dt.find_next_sibling("dd")
                        if not dd:
                            continue

                        # 作者
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

                        # 摘要（保持你原来的写法不动）
                        abstract_p = dd.find("p", class_="list-abstract")
                        abstract_raw = abstract_p.text.replace("Abstract:", "").strip() if abstract_p else ""
                        abstract = f"{full_arxiv_id}\n{abstract_raw}"

                        papers.append({
                            "title": title,
                            "author": author_str,
                            "link": link,
                            "abstract": abstract,
                            "type": type_val  # 严格按章节赋值 new / cross / replace
                        })
                    next_node = next_node.find_next_sibling()
                break

    return papers

# ============== 只抓取这两个分类的全部 new/cross/replace ==============
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
