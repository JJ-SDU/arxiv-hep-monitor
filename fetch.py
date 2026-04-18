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
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        h3 = soup.find("h3", string=lambda t: t and "Showing new listings for" in t)
        if h3:
            return h3.text.replace("Showing new listings for ", "").strip()
    except Exception as e:
        print(f"❌ 获取日期失败: {e}")
    return "No date"

# 获取日期
arxiv_date = get_arxiv_original_date("hep-ex")
print(f"📅 网页原始日期：{arxiv_date}")

# ============== 按章节精准抓取：new / cross / replace ==============
def fetch_papers_by_section(url, section_name):
    papers = []
    print(f"\n🔍 正在抓取章节：{section_name}")

    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return []

    # 找到对应章节标题
    for h3 in soup.find_all("h3"):
        if section_name in h3.text:
            # 关键修复：arXiv 真实结构是 h3 后直接跟 <dl id="articles">
            articles_dl = h3.find_next_sibling("dl", id="articles")
            if not articles_dl:
                print(f"⚠️ 警告：未找到 {section_name} 的文章列表")
                continue

            dts = articles_dl.find_all("dt")
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
                title_div = dd.find("div", class_="list-title mathjax")
                title = title_div.get_text(strip=True).replace("Title:", "").strip() if title_div else ""

                # PDF 链接
                link = f"https://arxiv.org/pdf/{arxiv_id}"

                # 关键修复：直接从列表页抓取摘要（真实标签是 p.mathjax）
                abstract_p = dd.find("p", class_="mathjax")
                summary = abstract_p.get_text(strip=True) if abstract_p else ""

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

# 写入文件（确保编码正确）
with open("output/data.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("\n🎉 抓取完成！new / cross / replace 全部正确抓取！")
