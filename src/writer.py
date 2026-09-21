import os
import requests
import json
from datetime import datetime

SYSTEM_PROMPT = """
你是一位专注全球人工智能与大模型（LLM）领域的资深科技主编，长期为顶级科技自媒体撰写公众号内容。
你的文风特点：客观严谨、兼具极高的技术洞察与通俗可读性，擅长提炼核心价值（“为什么这个模型重要”、“对开发者或行业意味着什么”），杜绝空洞的套话。

请根据提供的最新素材，撰写一篇图文并茂、排版精美的微信公众号图文。

【排版与格式要求（极其重要）】：
1. 微信公众号编辑器仅支持内联 CSS 样式（Inline CSS），因此你必须直接输出一段完整的、可直接粘贴到微信后台的 HTML 结构。
2. 严禁使用外部 CSS 类名（class），所有样式必须写在标签的 style 属性中。
3. 结构包含：
   - 顶部封面横幅图（由我提供占位，你保留即可）。
   - 导读摘要（用浅灰底色、圆角、精致边框的卡片包裹）。
   - 【核心头条 · 深度解读】（选 1~2 个最具突破性的大模型/算法，详细阐述技术原理与应用影响）。
   - 【开源热点 · 神兵利器】（选 2~3 个前沿开源模型或工具，列出核心功能与亮点）。
   - 【前沿论文 · 趋势速览】（学术前沿动态精粹）。
   - 【主编观点 / 总结思考】（1~2 句话总结今日技术趋势）。
4. 样式规范：
   - 全局字体：-apple-system-font, BlinkMacSystemFont, "Helvetica Neue", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
   - 正文字号：15px，行高：1.8，字间距：0.5px，颜色：#2d3748。
   - 二级标题（H2）：前置精致标签，字号 17px，加粗，主色调建议为高质感的科技蓝（#1a73e8）或紫色。
   - 强调与引用：重点文字加粗或使用高亮底色背景（例如 background-color: #fff3cd）。
   - 每个板块必须使用现代卡片式风格（border-radius: 8px, padding: 15px, background-color: #f7fafc, margin-bottom: 20px）。
5. 直接输出 HTML 代码片段（从包含整个文章的最外层 <section> 开始，到闭合的 </section> 结束），不要用 ```html ``` 这种 markdown 代码块包裹，也不要有任何额外的开场白或解释。
"""

def generate_wechat_article(news_content: str, model_name: str = "gemini-2.5-pro") -> str:
    """调用 Google Gemini API 生成排版好的微信 HTML 文章"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("缺少 GEMINI_API_KEY 环境变量！")

    today_str = datetime.now().strftime("%Y年%m月%d日")
    
    # 动态挑选一张高质量的科技感封面图 (Unsplash 科技主题)
    cover_image_url = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1200&q=80"

    user_prompt = f"""
今天日期：{today_str}
以下是过去 24 小时收集到的大模型领域最新素材：

{news_content}

请为本期《AI大模型前沿早报 | {today_str}》生成微信图文。
注意：请在正文最开头嵌入封面图：
<div style="margin-bottom: 20px; text-align: center;">
    <img src="{cover_image_url}" style="width: 100%; border-radius: 10px; display: block; box-shadow: 0 4px 12px rgba(0,0,0,0.08);" alt="AI封面" />
</div>
现在，请直接输出美化排版后的完整 HTML 内容：
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"{SYSTEM_PROMPT}\n\n{user_prompt}"}]
            }
        ],
        "generationConfig": {
            "temperature": 0.6,
            "maxOutputTokens": 8192
        }
    }

    headers = {"Content-Type": "application/json"}
    
    # 支持优先使用 gemini-2.5-pro，如果用户权限不同则 fallback 到 gemini-2.5-flash 或 gemini-1.5-pro
    models_to_try = [model_name, "gemini-2.5-flash", "gemini-1.5-pro"]
    
    last_error = None
    for m in models_to_try:
        try:
            req_url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
            response = requests.post(req_url, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                res_data = response.json()
                article_html = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                # 剔除可能存在的 ```html 包裹
                if article_html.startswith("```html"):
                    article_html = article_html[7:]
                if article_html.startswith("```"):
                    article_html = article_html[3:]
                if article_html.endswith("```"):
                    article_html = article_html[:-3]
                return article_html.strip()
            else:
                last_error = response.text
                print(f"尝试模型 {m} 失败: {response.status_code}, 正在尝试其他可用模型...")
        except Exception as e:
            last_error = str(e)
            
    raise RuntimeError(f"调用 Gemini 失败: {last_error}")
