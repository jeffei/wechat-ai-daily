import requests
import feedparser
from datetime import datetime, timezone
from typing import List, Dict

def fetch_huggingface_papers() -> List[Dict]:
    """抓取 Hugging Face Daily Papers 热门大模型论文"""
    url = "https://huggingface.co/api/daily_papers"
    papers = []
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for item in data[:5]:  # 取前 5 篇
                paper = item.get("paper", {})
                title = paper.get("title", "")
                summary = paper.get("summary", "")
                upvotes = item.get("upvotes", 0)
                papers.append({
                    "source": "Hugging Face Daily Papers",
                    "title": title,
                    "summary": summary[:300] + "...",
                    "upvotes": upvotes,
                    "url": f"https://huggingface.co/papers/{paper.get('id', '')}"
                })
    except Exception as e:
        print(f"Error fetching Hugging Face papers: {e}")
    return papers

def fetch_github_ai_trending() -> List[Dict]:
    """抓取 GitHub 最新热门的大模型/AI 开源项目"""
    url = "https://api.github.com/search/repositories?q=topic:llm+stars:>50&sort=updated&order=desc&per_page=6"
    repos = []
    try:
        headers = {"User-Agent": "wechat-ai-daily-bot"}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            items = resp.json().get("items", [])
            for item in items[:4]:
                repos.append({
                    "source": "GitHub Trending AI",
                    "title": item.get("full_name", ""),
                    "summary": item.get("description", "无描述"),
                    "stars": item.get("stargazers_count", 0),
                    "url": item.get("html_url", "")
                })
    except Exception as e:
        print(f"Error fetching GitHub trending: {e}")
    return repos

def fetch_arxiv_ai_rss() -> List[Dict]:
    """抓取 arXiv cs.CL (计算语言学/LLM) 最新论文 RSS"""
    url = "https://rss.arxiv.org/rss/cs.CL"
    papers = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:4]:
            papers.append({
                "source": "arXiv cs.CL",
                "title": entry.title.replace("\n", " ").strip(),
                "summary": entry.summary.replace("\n", " ")[:260] + "...",
                "url": entry.link
            })
    except Exception as e:
        print(f"Error fetching arXiv: {e}")
    return papers

def aggregate_news() -> str:
    """聚合所有资讯并整理为 Markdown 文本供 Gemini 消化"""
    hf_papers = fetch_huggingface_papers()
    gh_repos = fetch_github_ai_trending()
    arxiv_papers = fetch_arxiv_ai_rss()

    content_parts = []
    content_parts.append(f"# 今日大模型前沿原始素材聚合（抓取时间：{datetime.now().strftime('%Y-%m-%d')}）\n")

    if hf_papers:
        content_parts.append("## 1. Hugging Face 社区热议大模型与论文：")
        for idx, p in enumerate(hf_papers, 1):
            content_parts.append(f"{idx}. **{p['title']}** (点赞数: {p.get('upvotes', 0)})\n   - 简介: {p['summary']}\n   - 链接: {p['url']}")

    if gh_repos:
        content_parts.append("\n## 2. GitHub 活跃热门开源 LLM 架构与工具：")
        for idx, r in enumerate(gh_repos, 1):
            content_parts.append(f"{idx}. **{r['title']}** (Stars: {r.get('stars', 0)})\n   - 描述: {r['summary']}\n   - 链接: {r['url']}")

    if arxiv_papers:
        content_parts.append("\n## 3. arXiv 最新前沿自然语言与大模型研究：")
        for idx, a in enumerate(arxiv_papers, 1):
            content_parts.append(f"{idx}. **{a['title']}**\n   - 摘要: {a['summary']}\n   - 链接: {a['url']}")

    return "\n".join(content_parts)

if __name__ == "__main__":
    print(aggregate_news())
