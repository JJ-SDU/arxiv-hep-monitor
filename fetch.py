import json
import os
import requests
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

# 获取日期
arxiv_date = get_arxiv_original_date("hep-ex")
print(f"📅 网页原始日期：{arxiv_date}")

# ============== 按章节精准抓取：new / cross / replace ==============
def fetch_papers_by_section(url, section_name):
    try:
        response = requests.get(url, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
    except:
        return []

    papers = []
    print(f"\n🔍 正在抓取章节：{section_name}")

    # 找到对应章节标题
    for h3 in soup.find_all("h3"):
        if section_name in h3.text:
            list_items = h3.find_next_sibling("div", class_="list-items")
            if not list_items:
                continue

            dts = list_items.find_all("dt")
            print(f"📄 找到文章数量：{len(dts)}")

            for idx, dt in enumerate(dts):
                id_a = dt.find("a", title="Abstract")
                if not id_a:
                    continue

                arxiv_id = id_a["href"].split("/")[-1]
                full_arxiv_id = f"arXiv:{arxiv_id}"
                dd = dt.find_next_sibling("dd")
                if not dd:
                    continue

                # 作者
                author_div = dd.find("div", class_="list-authors")
                author_str = author_div.get_text(strip=True).replace("Authors:", "").strip() if author_div else "Unknown"

                # 标题
                title_div = dd.find("div", class_="list-title")
                title = title_div.get_text(strip=True).replace("Title:", "").strip() if title_div else ""

                # PDF 链接
                link = f"https://arxiv.org/pdf/{arxiv_id}"

                # ===================== 【唯一修改：正确抓取摘要】 =====================
                abstract_url = f"https://arxiv.org/abs/{arxiv_id}"
                try:
                    abs_resp = requests.get(abstract_url, timeout=8)
                    abs_soup = BeautifulSoup(abs_resp.text, "html.parser")
                    blockquote = abs_soup.find("blockquote", class_="abstract")
                    if blockquote:
                        summary = blockquote.get_text(strip=True).replace("Abstract:", "").strip()
                    else:
                        summary = ""
                except:
                    summary = ""
                # ========================================================================

                papers.append({
                    "title": title,
                    "author": author_str,
                    "link": link,
                    "arXiv number": full_arxiv_id,
                    "summary": summary
                })
                print(f"  ✅ 已抓取第 {idx+1} 篇：{arxiv_id}")
            break
    return papers

# ============== 抓取 hep-ex / hep-ph 的三类文章 ==============
def fetch_category(category):
    url = f"https://arxiv.org/list/{category}/new"
    return {
        "new": fetch_papers_by_section(url, "New submissions"),
        "cross": fetch_papers_by_section(url, "Cross submissions"),
        "replace": fetch_papers_by_section(url, "Replacement submissions")
    }

# ============== 主逻辑 ==============
result = {
    "date": arxiv_date,
    "hep-ex": fetch_category("hep-ex"),
    "hep-ph": fetch_category("hep-ph")
}

# 打印统计
for cat in ["hep-ex", "hep-ph"]:
    data = result[cat]
    n = len(data["new"])
    c = len(data["cross"])
    r = len(data["replace"])
    print(f"\n✅ {cat}: new={n} cross={c} replace={r} 总计={n+c+r}")

# 写入文件
with open("output/data.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

os.utime("output/data.json", None)
print("\n🎉 抓取完成！摘要已全部成功抓取！")
