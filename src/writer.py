import os
import requests
import json
from datetime import datetime

SYSTEM_PROMPT = """
你是一位顶尖的 AI 科技自媒体资深主编，专注于全球大模型（LLM）与人工智能领域的重大科技新闻报道。
你的受众是关注 AI 发展脉搏的技术人、创业者与数码科技爱好者。

【文风与定位】：
- 聚焦“硬核科技新闻”：有热点、有深度、有商业与技术洞察。
- 拒绝平铺直叙的翻译，提炼出：“发生了什么”、“对大模型格局有何冲击”、“普通人或开发者能用它做什么”。
- 语言生动鲜明、排版清爽大气。

【排版规范（微信公众号必须是内联 CSS）】：
1. 严禁外部 CSS，必须全部使用行内 style 属性。
2. 板块结构规范：
   - 顶部科技封面图（保留提供的图片占位）。
   - 【今日风向标】（浅灰/浅蓝圆角卡片，用 2~3 句话高度概括当期最重磅看点）。
   - 【焦点头条 · 重磅大事件】（深度剖析 1~2 个最轰动的大模型重大新闻）。
   - 【大厂与开源风云】（OpenAI、Google、Anthropic、DeepSeek、Meta 等最新产品、模型迭代或重大商业动作）。
   - 【前沿落地与行业观察】（模型新功能、算力/芯片动态、投资或争议）。
   - 【主编锐评】（1 段有独立视角的精辟总结）。
3. 样式要求：
   - 正文：font-size: 15px; line-height: 1.8; color: #2d3748; letter-spacing: 0.5px;
   - 标题：font-size: 17px; font-weight: bold; color: #1a73e8; margin-bottom: 10px;
   - 卡片框：background-color: #f8fafc; border-left: 4px solid #1a73e8; border-radius: 8px; padding: 16px; margin-bottom: 22px;
   - 重点句子：使用加粗或淡黄色/浅蓝色背景高亮（background-color: #fef3c7; padding: 1px 4px; border-radius: 3px;）。
4. 直接输出以 <section> 开始、</section> 闭合的 HTML，不要任何 ```html 标记，也不要有任何客套解释。
"""

def generate_wechat_article(news_content: str, model_name: str = "gemini-2.5-pro") -> str:
    """调用 Google Gemini API 生成大模型科技新闻图文"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("缺少 GEMINI_API_KEY 环境变量！")

    today_str = datetime.now().strftime("%Y年%m月%d日")
    cover_image_url = "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=1200&q=80"

    user_prompt = f"""
今天日期：{today_str}
以下是最新采集到的全球 AI & 大模型重大科技新闻素材：

{news_content}

请为本期《AI大模型科技观察 | {today_str}》撰写一篇极具吸引力、图文并茂的微信科技新闻推文。
注意：请在正文最开头嵌入封面图：
<div style="margin-bottom: 22px; text-align: center;">
    <img src="{cover_image_url}" style="width: 100%; border-radius: 10px; display: block; box-shadow: 0 4px 14px rgba(0,0,0,0.08);" alt="AI科技前沿" />
</div>

请严格遵守内联 CSS 排版规范，直接输出完整 HTML：
"""

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"{SYSTEM_PROMPT}\n\n{user_prompt}"}]
            }
        ],
        "generationConfig": {
            "temperature": 0.5,
            "maxOutputTokens": 8192
        }
    }

    models_to_try = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
    last_error = None
    for m in models_to_try:
        try:
            print(f"🤖 正在尝试调用 Gemini 模型: {m} ...")
            req_url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
            response = requests.post(req_url, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                res_data = response.json()
                article_html = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                if article_html.startswith("```html"):
                    article_html = article_html[7:]
                if article_html.startswith("```"):
                    article_html = article_html[3:]
                if article_html.endswith("```"):
                    article_html = article_html[:-3]
                print(f"🎉 模型 {m} 生成成功！")
                return article_html.strip()
            else:
                last_error = f"HTTP {response.status_code}: {response.text}"
                print(f"⚠️ 模型 {m} 返回错误: {last_error}，切换备选模型...")
        except Exception as e:
            last_error = str(e)
            print(f"⚠️ 模型 {m} 请求异常: {last_error}，切换备选模型...")
            
    raise RuntimeError(f"调用 Gemini 所有模型均失败: {last_error}")
