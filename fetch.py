import json
import os
import requests
from bs4 import BeautifulSoup

os.makedirs("output", exist_ok=True)

def fetch_papers(category):
    url = f"https://arxiv.org/list/{category}/new"
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"❌ 请求 {url} 失败: {e}")
        return []

    papers = []
    dts = soup.find_all("dt")
    dds = soup.find_all("dd")

    if len(dts) != len(dds):
        print(f"⚠️ {category} 中 dt/dd 数量不匹配")

    for i, dt in enumerate(dts):
        dd = dds[i] if i < len(dds) else None
        if not dd:
            continue

        # 1. arXiv 编号
        id_span = dt.find("span", class_="list-identifier")
        if not id_span:
            continue
        arxiv_num = id_span.text.strip().split()[0]

        # 2. Announce type（从括号里取）
        announce_type = ""
        sup_tag = id_span.find("sup")
        if sup_tag:
            announce_type = sup_tag.text.strip("()")

        # 3. 标题
        title_tag = dd.find("div", class_="list-title")
        title = title_tag.text.replace("Title:", "").strip() if title_tag else ""

        # 4. 作者（完整列表）
        authors = []
        author_div = dd.find("div", class_="list-authors")
        if author_div:
            for a in author_div.find_all("a"):
                authors.append(a.text.strip())
        author_str = ", ".join(authors) if authors else "Unknown"

        # 5. 链接
        link = f"https://arxiv.org/abs/{arxiv_num.split(':')[-1]}"

        # 6. 摘要（修复空摘要问题）
        abstract_tag = dd.find("p", class_="list-abstract")
        summary = abstract_tag.text.replace("Abstract:", "").strip() if abstract_tag else ""

        papers.append({
            "title": title,
            "author": author_str,
            "link": link,
            "arXiv number": arxiv_num,
            "Announce type": announce_type,
            "category": category,
            "summary": summary
        })
    return papers

if __name__ == "__main__":
    categories = ["hep-ex", "hep-ph"]
    result = {
        "date": "",
        "hep-ex": [],
        "hep-ph": []
    }

    # 取第一个页面的日期
    try:
        date_url = "https://arxiv.org/list/hep-ex/new"
        date_resp = requests.get(date_url, timeout=10)
        date_soup = BeautifulSoup(date_resp.text, "html.parser")
        h3 = date_soup.find("h3", string=lambda t: t and "Showing new listings for" in t)
        if h3:
            result["date"] = h3.text.replace("Showing new listings for ", "").strip()
    except:
        result["date"] = "Unknown"

    for cat in categories:
        papers = fetch_papers(cat)
        result[cat] = papers
        print(f"✅ {cat} 抓取完成：{len(papers)} 篇")

    with open("output/data.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("\n🎉 全部抓取完成！")
