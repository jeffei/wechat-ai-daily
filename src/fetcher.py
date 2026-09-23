import requests
import feedparser
import time
import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict

# 顶级 AI 巨头与前沿大模型核心关键词库（高权重）
TOP_TIER_KEYWORDS = [
    "openai", "google", "gemini", "anthropic", "claude", "deepseek", 
    "qwen", "通义千问", "meta", "llama", "nvidia", "英伟达", "microsoft", 
    "apple", "xai", "grok", "mistral", "blackwell", "gpt"
]

# 行业重大突破与轰动事件关键词库
IMPACT_KEYWORDS = [
    "billion", "million", "funding", "raises", "launch", "unveils", 
    "releases", "breakthrough", "chip", "gpu", "lawsuit", "acquire", 
    "acquisition", "autonomous", "agent", "supercomputer", "open source",
    "融资", "发布", "突破", "开源", "和解", "芯片", "算力", "首款"
]

def get_time_window_hours() -> int:
    """
    根据发布日程动态计算时间窗口：
    周一 (weekday 0) 覆盖过去 72 小时（涵盖周五、周六、周日）
    周三/周五 覆盖过去 48 小时
    """
    now = datetime.now()
    if now.weekday() == 0:
        return 72
    return 48

def calculate_virality_score(title: str, summary: str, base_bonus: int = 0) -> int:
    """计算新闻的行业热度与轰动指数"""
    text = (title + " " + summary).lower()
    score = base_bonus
    
    # 命中顶级科技巨头
    for kw in TOP_TIER_KEYWORDS:
        if kw in text:
            score += 15
            
    # 命中重大商业/技术突破关键词
    for kw in IMPACT_KEYWORDS:
        if kw in text:
            score += 10
            
    # 标题含大额数字或首创
    if re.search(r'\$\d+(\.\d+)?\s*(billion|million|b|m)', text) or "首个" in text or "首次" in text:
        score += 15
        
    return score

def fetch_rss_news_in_window(feed_url: str, source_name: str, window_hours: int) -> List[Dict]:
    """抓取指定时间窗口内的 RSS 新闻，并计算热度评分"""
    news_items = []
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get(feed_url, headers=headers, timeout=12)
        if resp.status_code == 200:
            feed = feedparser.parse(resp.content)
            for entry in feed.entries:
                # 解析发布时间
                published_dt = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published_dt = datetime.fromtimestamp(time.mktime(entry.published_parsed), tz=timezone.utc)
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    published_dt = datetime.fromtimestamp(time.mktime(entry.updated_parsed), tz=timezone.utc)
                
                # 时间窗口过滤：超过 48h/72h 的直接舍弃
                if published_dt and published_dt < cutoff_time:
                    continue
                
                # 文本清洗
                summary = entry.get("summary", "") or entry.get("description", "")
                if "<" in summary:
                    summary = re.sub(r'<[^>]+>', '', summary)
                summary = summary.replace("\n", " ").strip()
                title = entry.get("title", "").strip()
                
                # 计算火爆热度得分
                score = calculate_virality_score(title, summary, base_bonus=10)
                
                news_items.append({
                    "source": source_name,
                    "title": title,
                    "summary": summary[:280] + "..." if len(summary) > 280 else summary,
                    "url": entry.get("link", ""),
                    "score": score,
                    "published_at": published_dt.strftime("%Y-%m-%d %H:%M UTC") if published_dt else "近期"
                })
    except Exception as e:
        print(f"抓取 {source_name} 失败: {e}")
    return news_items

def fetch_hacker_news_viral(window_hours: int) -> List[Dict]:
    """通过 Hacker News 官方检索 API 获取全网讨论度极高的爆款 AI 新闻 (点赞>50)"""
    viral_items = []
    since_timestamp = int(time.time()) - (window_hours * 3600)
    url = f"https://hn.algolia.com/api/v1/search_by_date?query=AI+OR+LLM+OR+OpenAI+OR+Gemini+OR+Anthropic+OR+DeepSeek&tags=story&numericFilters=points>50,created_at_i>{since_timestamp}"
    
    try:
        resp = requests.get(url, timeout=12)
        if resp.status_code == 200:
            hits = resp.json().get("hits", [])
            for hit in hits:
                title = hit.get("title", "").strip()
                points = hit.get("points", 0)
                comments = hit.get("num_comments", 0)
                link = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
                
                # HN 的真实点赞和评论直接加权为火爆指数
                score = calculate_virality_score(title, "", base_bonus=points + comments)
                
                viral_items.append({
                    "source": "Hacker News 热议",
                    "title": title,
                    "summary": f"社区高赞热度: {points} Points，{comments} 条专业深度讨论",
                    "url": link,
                    "score": score,
                    "published_at": "近期爆款"
                })
    except Exception as e:
        print(f"抓取 Hacker News 爆款失败: {e}")
    return viral_items

def fetch_huggingface_viral() -> List[Dict]:
    """抓取 Hugging Face 点赞最高、引发学术界轰动的热门模型动态"""
    items = []
    url = "https://huggingface.co/api/daily_papers"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            # 按社区点赞量倒序排序，筛选出真正破圈的高赞研究
            sorted_papers = sorted(data, key=lambda x: x.get("upvotes", 0), reverse=True)
            for item in sorted_papers[:4]:
                paper = item.get("paper", {})
                upvotes = item.get("upvotes", 0)
                title = paper.get("title", "")
                summary = paper.get("summary", "")[:220] + "..."
                
                score = calculate_virality_score(title, summary, base_bonus=upvotes * 3)
                
                items.append({
                    "source": "Hugging Face 高赞前沿",
                    "title": title,
                    "summary": f"[高赞数: {upvotes}] {summary}",
                    "url": f"https://huggingface.co/papers/{paper.get('id', '')}",
                    "score": score,
                    "published_at": "今日高赞"
                })
    except Exception as e:
        print(f"抓取 Hugging Face 失败: {e}")
    return items

def aggregate_news() -> str:
    """
    全面聚合指定时间窗口内（48h / 72h）全网热度最高、最轰动的大模型重大新闻
    """
    window_hours = get_time_window_hours()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"🕒 当前触发时间窗口: 过去 {window_hours} 小时全网资讯（当前时间: {now_str}）")
    
    candidate_pool = []
    
    # 1. 抓取 TechCrunch、VentureBeat、The Verge 48h/72h 内的全部候选
    print("📡 正在采集 TechCrunch AI...")
    candidate_pool.extend(fetch_rss_news_in_window("https://techcrunch.com/category/artificial-intelligence/feed/", "TechCrunch AI", window_hours))
    
    print("📡 正在采集 VentureBeat AI...")
    candidate_pool.extend(fetch_rss_news_in_window("https://venturebeat.com/category/ai/feed/", "VentureBeat AI", window_hours))
    
    print("📡 正在采集 The Verge AI...")
    candidate_pool.extend(fetch_rss_news_in_window("https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "The Verge AI", window_hours))

    # 2. 抓取全球开发者社区爆款热点（Hacker News 50+赞 与 Hugging Face 高赞）
    print("🔥 正在获取 Hacker News 爆款 AI 讨论...")
    candidate_pool.extend(fetch_hacker_news_viral(window_hours))
    
    print("🌟 正在获取 Hugging Face 顶尖高赞研究...")
    candidate_pool.extend(fetch_huggingface_viral())

    print(f"📊 在过去 {window_hours} 小时内共初筛出 {len(candidate_pool)} 篇候选资讯。")

    # 3. 核心算法：按“火爆度与行业影响力评分（score）”从高到低严格倒序排列！
    candidate_pool.sort(key=lambda x: x["score"], reverse=True)

    # 4. 精选前 12 篇最具轰动效应与破圈影响力的超级热点输入给 Gemini
    top_candidates = candidate_pool[:12]

    content_parts = [
        f"# 全球 AI 大模型重大科技新闻精选池（覆盖时间窗口：过去 {window_hours} 小时）\n"
        f"> 提示：以下候选资讯已通过全网热度算法完成权重排序（得分越高，代表全网讨论度与行业轰动度越大）。\n"
    ]
    
    for idx, item in enumerate(top_candidates, 1):
        content_parts.append(
            f"### [{idx}] 【{item['source']} | 热度分: {item['score']}】{item['title']}\n"
            f"- 发布时间: {item['published_at']}\n"
            f"- 核心要点: {item['summary']}\n"
            f"- 来源链接: {item['url']}\n"
        )

    return "\n".join(content_parts)

if __name__ == "__main__":
    print(aggregate_news())
