import requests
import feedparser
from datetime import datetime
from typing import List, Dict

def fetch_rss_news(feed_url: str, source_name: str, max_items: int = 5) -> List[Dict]:
    """通用 RSS 抓取函数"""
    news = []
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get(feed_url, headers=headers, timeout=12)
        if resp.status_code == 200:
            feed = feedparser.parse(resp.content)
            for entry in feed.entries[:max_items]:
                # 清洗摘要中的 HTML 标签
                summary = entry.get("summary", "") or entry.get("description", "")
                if "<" in summary:
                    import re
                    summary = re.sub(r'<[^>]+>', '', summary)
                summary = summary.replace("\n", " ").strip()
                
                news.append({
                    "source": source_name,
                    "title": entry.get("title", "").strip(),
                    "summary": summary[:280] + "..." if len(summary) > 280 else summary,
                    "url": entry.get("link", "")
                })
    except Exception as e:
        print(f"抓取 {source_name} 失败: {e}")
    return news

def fetch_huggingface_trending() -> List[Dict]:
    """抓取 Hugging Face 社区点赞最高的新大模型动态"""
    url = "https://huggingface.co/api/daily_papers"
    items = []
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for item in data[:3]:
                paper = item.get("paper", {})
                items.append({
                    "source": "Hugging Face 社区热点",
                    "title": paper.get("title", ""),
                    "summary": (paper.get("summary", "")[:200] + "..."),
                    "url": f"https://huggingface.co/papers/{paper.get('id', '')}"
                })
    except Exception as e:
        print(f"抓取 Hugging Face 失败: {e}")
    return items

def aggregate_news() -> str:
    """全面聚合全球 AI 大模型重大科技新闻"""
    all_news = []
    
    # 1. TechCrunch 人工智能科技快讯 (权威、深度)
    print("正在抓取 TechCrunch AI 新闻...")
    all_news.extend(fetch_rss_news("https://techcrunch.com/category/artificial-intelligence/feed/", "TechCrunch AI", max_items=4))
    
    # 2. VentureBeat 专注企业级 AI 与大模型商业化报道
    print("正在抓取 VentureBeat AI 新闻...")
    all_news.extend(fetch_rss_news("https://venturebeat.com/category/ai/feed/", "VentureBeat AI", max_items=4))

    # 3. The Verge 前沿科技消费与大模型大事件
    print("正在抓取 The Verge AI 新闻...")
    all_news.extend(fetch_rss_news("https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "The Verge AI", max_items=3))

    # 4. Hugging Face 顶级前沿模型突破
    print("正在抓取 Hugging Face 趋势...")
    all_news.extend(fetch_huggingface_trending())

    # 汇总组织为大模型结构化文本
    today_str = datetime.now().strftime('%Y-%m-%d')
    content_parts = [f"# 今日全球 AI & 大模型最新科技新闻动态（聚合时间：{today_str}）\n"]
    
    for idx, item in enumerate(all_news, 1):
        content_parts.append(
            f"### [{idx}] 【{item['source']}】{item['title']}\n"
            f"- 核心要点: {item['summary']}\n"
            f"- 来源链接: {item['url']}\n"
        )

    return "\n".join(content_parts)

if __name__ == "__main__":
    print(aggregate_news())
