import os
import requests
import json
import re
from datetime import datetime
from typing import Tuple, List

SYSTEM_PROMPT = """
你是一位顶尖的 AI 科技自媒体资深主编，专注于全球大模型（LLM）与人工智能领域的重大科技新闻报道。
你的受众是关注 AI 发展脉搏的技术人、创业者与数码科技爱好者。

【任务要求】：
请根据提供的最新科技资讯素材，输出两部分内容：
第一部分：3~4 条极具冲击力的【核心速览要点】（用于生成审核摘要长图，每条 30~50 字，提炼出最核心的发布或技术突破）。
第二部分：一篇排版精美、使用内联 CSS 的完整微信公众号图文。

【输出格式分隔规范（务必严格遵循）】：
===HIGHLIGHTS===
1. [要点1简述]
2. [要点2简述]
3. [要点3简述]
===ARTICLE===
<section style="...">
...这里是完整的微信文章 HTML...
</section>

【核心排版规范与禁止项（极其重要）】：
1. 严禁事项：
   - ❌ 绝对严禁给板块大标题添加全宽度的矩形外边框（例如严禁使用 border: 1px solid #... 包裹标题）！你之前生成的标题被套上了一个居中的大空心方框，极其难看！
   - ❌ 严禁标题居中对齐，所有标题一律靠左对齐。
2. 板块主标题（H2）标准样式（必须严格使用以下 HTML 胶囊标签结构）：
   <div style="margin: 30px 0 16px 0; text-align: left;">
       <span style="display: inline-block; background-color: #ebf3fe; color: #1a73e8; font-size: 16px; font-weight: bold; padding: 6px 14px; border-radius: 6px; letter-spacing: 0.5px;">
           🔥 焦点头条 · 深度解读
       </span>
   </div>
3. 每条新闻必须使用独立的浅底色精致卡片包裹：
   <div style="background-color: #f8fafc; border-left: 4px solid #1a73e8; border-radius: 8px; padding: 16px 18px; margin-bottom: 20px;">
       <h3 style="margin: 0 0 10px 0; font-size: 16px; font-weight: bold; color: #1a202c; line-height: 1.4;">
           1. 谷歌 Googlebook 问世：899 美元的“Gemini 载体”
       </h3>
       <p style="margin: 0 0 10px 0; font-size: 15px; line-height: 1.8; color: #4a5568; letter-spacing: 0.5px;">
           [正文内容，重点词句可用 <span style="background-color: #fef3c7; padding: 1px 4px; border-radius: 3px; font-weight: bold;">高亮标记</span>]
       </p>
   </div>
4. 包含模块：
   - 顶部封面图
   - 【今日风向标】（浅灰导读卡片）
   - 【焦点头条 · 深度解读】（胶囊标 + 新闻卡片）
   - 【大厂与开源风云】（胶囊标 + 新闻卡片）
   - 【前沿落地与商业观察】（胶囊标 + 新闻卡片）
   - 【主编锐评】（总结卡片）
"""

def clean_wechat_html(html_code: str) -> str:
    """后处理清洗：彻底消除可能出现的居中空心边框标题与异常外框"""
    # 消除诸如 border: 1px solid ... text-align: center 的标题方框，转换为精美胶囊标题
    pattern = r'<div[^>]*border\s*:\s*1px\s*solid[^>]*text-align\s*:\s*center[^>]*>(.*?)</div>'
    def replacer(match):
        text = re.sub(r'<[^>]+>', '', match.group(1)).strip()
        return f'<div style="margin: 28px 0 14px 0; text-align: left;"><span style="display: inline-block; background-color: #ebf3fe; color: #1a73e8; font-size: 16px; font-weight: bold; padding: 6px 14px; border-radius: 6px; letter-spacing: 0.5px;">📌 {text}</span></div>'
    
    cleaned = re.sub(pattern, replacer, html_code, flags=re.IGNORECASE | re.DOTALL)
    return cleaned

def get_available_models(api_key: str) -> List[str]:
    """动态查询当前 API Key 授权的所有可用模型，严格过滤只保留 gemini-3 系列"""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            models_data = resp.json().get("models", [])
            valid_models = []
            for m in models_data:
                name = m.get("name", "").replace("models/", "")
                methods = m.get("supportedGenerationMethods", [])
                # 严格限定：只允许 gemini-3 系列，坚决剔除 2 开头、1 开头和 3.5
                if "generateContent" in methods and name.startswith("gemini-3") and "3.5" not in name:
                    valid_models.append(name)
            return valid_models
        else:
            print(f"⚠️ 查询可用模型列表返回: HTTP {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"⚠️ 查询可用模型列表失败: {e}")
    return []

def generate_wechat_article(news_content: str, model_name: str = "gemini-3.8-flash") -> Tuple[str, List[str]]:
    """调用 Google Gemini 生成微信图文与要点摘要，返回 (article_html, highlights)"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("缺少 GEMINI_API_KEY 环境变量！")

    import time
    
    print("🔍 正在动态检测当前 API Key 支持的可用模型...")
    available_models = get_available_models(api_key)
    print(f"📋 经严格过滤后的 Gemini 3.x 系列授权可用模型:\n{json.dumps(available_models, ensure_ascii=False, indent=2)}")

    today_str = datetime.now().strftime("%Y年%m月%d日")
    cover_image_url = "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=1200&q=80"

    user_prompt = f"""
今天日期：{today_str}
以下是最新采集到的全球 AI & 大模型重大科技新闻素材：

{news_content}

请为本期《AI大模型科技观察 | {today_str}》撰写微信科技新闻推文及海报速览要点。
注意：在 HTML 文章最开头嵌入封面图：
<div style="margin-bottom: 22px; text-align: center;">
    <img src="{cover_image_url}" style="width: 100%; border-radius: 10px; display: block; box-shadow: 0 4px 14px rgba(0,0,0,0.08);" alt="AI科技前沿" />
</div>

请严格遵循 ===HIGHLIGHTS=== 与 ===ARTICLE=== 分隔符输出：
"""

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{SYSTEM_PROMPT}\n\n{user_prompt}"}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.5,
            "maxOutputTokens": 8192
        }
    }

    # 严密构建降级备选队列：3.8 始终第一，3.6 始终第二，绝对不调用任何 2.x 模型
    candidate_queue = []
    
    # 1. 首选 3.8-flash
    if model_name in available_models:
        candidate_queue.append(model_name)
    else:
        for m in available_models:
            if "3.8" in m and m not in candidate_queue:
                candidate_queue.append(m)
        if model_name not in candidate_queue:
            candidate_queue.append(model_name)

    # 2. 次选 3.6-flash
    for m in available_models:
        if "3.6" in m and m not in candidate_queue:
            candidate_queue.append(m)
    if "gemini-3.6-flash" not in candidate_queue:
        candidate_queue.append("gemini-3.6-flash")

    # 3. 其他所有经过过滤的 3.x 可用模型
    for m in available_models:
        if m not in candidate_queue:
            candidate_queue.append(m)

    print(f"🚦 最终降级执行链（无任何 2.x 模型）: {' ➔ '.join(candidate_queue)}")

    last_error = None
    for m in candidate_queue:
        print(f"\n🚀 正在尝试调用模型: {m} ...")
        req_url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
        
        for attempt in range(1, 4):
            try:
                response = requests.post(req_url, headers=headers, json=payload, timeout=75)
                if response.status_code == 200:
                    res_data = response.json()
                    full_text = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    
                    # 解析 Highlights 与 Article
                    highlights = []
                    article_html = full_text
                    
                    if "===HIGHLIGHTS===" in full_text and "===ARTICLE===" in full_text:
                        parts = full_text.split("===ARTICLE===")
                        hl_text = parts[0].replace("===HIGHLIGHTS===", "").strip()
                        article_html = parts[1].strip()
                        for line in hl_text.split("\n"):
                            line = line.strip()
                            if line:
                                # 移除开头的 1. 2. - * 等标记
                                clean_line = re.sub(r'^\d+[\.、\s\-]+', '', line).strip()
                                if clean_line:
                                    highlights.append(clean_line)
                    else:
                        highlights = [
                            "全球主流大模型最新版本密集迭代，多模态推理能力显著提升",
                            "开源社区大模型活跃度再创新高，开发者工具链加速演进",
                            "AI 算力与商业化落地进入深水区，头部企业商业模式逐步成型"
                        ]

                    if article_html.startswith("```html"):
                        article_html = article_html[7:]
                    if article_html.startswith("```"):
                        article_html = article_html[3:]
                    article_html = clean_wechat_html(article_html.strip())
                    print(f"🎉 模型 [{m}] 生成成功并完成排版美化！共解析出 {len(highlights)} 条速览要点。")
                    return article_html, highlights

                elif response.status_code in (503, 429):
                    last_error = f"HTTP {response.status_code}: {response.text}"
                    print(f"⏳ 模型 [{m}] 临时高峰 (HTTP {response.status_code})，详细返回: {response.text.strip()}")
                    print(f"等待 {attempt * 4} 秒后进行第 {attempt}/3 次重试...")
                    time.sleep(attempt * 4)
                else:
                    last_error = f"HTTP {response.status_code}: {response.text}"
                    print(f"⚠️ 模型 [{m}] 返回具体错误: {last_error}")
                    break
            except Exception as e:
                last_error = str(e)
                print(f"⚠️ 模型 [{m}] 网络异常: {last_error}")
                time.sleep(3)
            
    raise RuntimeError(f"调用所有 Gemini 3.x 模型均失败，最后详细错误: {last_error}")
