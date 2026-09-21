import os
import requests
import json
import re
from datetime import datetime
from typing import Tuple, List

SYSTEM_PROMPT = """
你是一位顶级科技自媒体资深主编，专门运营千万级读者的 AI 大模型微信公众号。
你的排版风格被读者公认为“最舒适、最耐看、排版高级感十足”的标杆。

【核心任务】：
请根据最新科技资讯素材，提炼并输出以下四部分内容：
1. ===TITLE===：一个极具吸引力、专业高级且符合微信公众号调性的推文主标题（控制在 30 字以内，兼顾重磅新闻与核心看点）。
2. ===DIGEST===：一段微信推文摘要（50~80 字，言简意赅，用于公众号后台的“摘要”栏）。
3. ===HIGHLIGHTS===：3~4 条用于生成速览海报长图的极简看点（每条 30~50 字）。
4. ===ARTICLE===：整篇排版极其舒适、使用内联 CSS 的微信公众号 HTML 图文。

【输出格式分隔规范（务必严格遵循）】：
===TITLE===
[这里是推荐标题，例如：谷歌首款AI电脑问世！苹果2.5亿和解虚假宣传案 | AI前沿早报]
===DIGEST===
[这里是推荐摘要，例如：从Googlebook问世到苹果Siri虚假宣传案和解，一文纵览过去24小时全球大模型商业与技术重大动向。]
===HIGHLIGHTS===
1. [要点1简述]
2. [要点2简述]
3. [要点3简述]
===ARTICLE===
<section style="font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif; font-size: 15px; color: #333333; line-height: 1.85; letter-spacing: 0.5px;">
...这里是完整的微信文章 HTML...
</section>

【最舒适的微信科技排版黄金规范】：
1. 严禁事项：
   - ❌ 绝对严禁给标题添加居中空心边框（如 border: 1px solid）！所有标题必须左对齐。
   - ❌ 严禁出现大段密密麻麻的未分段文字。
2. 模块主标题（H2）：一律采用微圆角科技蓝胶囊标签：
   <div style="margin: 32px 0 16px 0; text-align: left;">
       <span style="display: inline-block; background-color: #ebf3fe; color: #1a73e8; font-size: 16px; font-weight: bold; padding: 6px 14px; border-radius: 6px; letter-spacing: 0.5px;">
           🔥 焦点头条 · 深度解读
       </span>
   </div>
3. 单条新闻卡片：使用柔和浅灰底色 + 左侧科技蓝微装饰线：
   <div style="background-color: #f8fafc; border-left: 4px solid #1a73e8; border-radius: 8px; padding: 18px 20px; margin-bottom: 22px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
       <h3 style="margin: 0 0 12px 0; font-size: 16px; font-weight: bold; color: #1a202c; line-height: 1.45;">
           1. 谷歌 Googlebook 问世：899 美元的“Gemini 载体”
       </h3>
       <p style="margin: 0 0 10px 0; font-size: 15px; line-height: 1.85; color: #4a5568; text-align: justify;">
           [正文，核心数据或结论可用 <span style="background-color: #fef3c7; color: #92400e; padding: 2px 5px; border-radius: 4px; font-weight: bold;">高亮标记</span>]
       </p>
   </div>
4. 包含模块：
   - 顶部科技封面图
   - 【今日风向标】（浅灰导读卡片）
   - 【焦点头条 · 深度解读】（胶囊标 + 新闻卡片）
   - 【大厂与开源风云】（胶囊标 + 新闻卡片）
   - 【前沿落地与商业观察】（胶囊标 + 新闻卡片）
   - 【主编锐评】（总结卡片）
"""

def clean_wechat_html(html_code: str) -> str:
    """彻底消除可能出现的任何居中空心边框标题与异常方框"""
    pattern = r'<div[^>]*border\s*:\s*1px\s*solid[^>]*text-align\s*:\s*center[^>]*>(.*?)</div>'
    def replacer(match):
        text = re.sub(r'<[^>]+>', '', match.group(1)).strip()
        return f'<div style="margin: 28px 0 14px 0; text-align: left;"><span style="display: inline-block; background-color: #ebf3fe; color: #1a73e8; font-size: 16px; font-weight: bold; padding: 6px 14px; border-radius: 6px; letter-spacing: 0.5px;">📌 {text}</span></div>'
    return re.sub(pattern, replacer, html_code, flags=re.IGNORECASE | re.DOTALL)

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
                if "generateContent" in methods and name.startswith("gemini-3") and "3.5" not in name:
                    valid_models.append(name)
            return valid_models
        else:
            print(f"⚠️ 查询可用模型列表返回: HTTP {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"⚠️ 查询可用模型列表失败: {e}")
    return []

def generate_wechat_article(news_content: str, model_name: str = "gemini-3.8-flash") -> Tuple[str, str, str, List[str]]:
    """
    调用 Google Gemini 生成微信图文
    返回: (title, digest, article_html, highlights)
    """
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

请为本期微信公众号推文生成：
1. 爆款推荐标题 (===TITLE===)
2. 推荐摘要 (===DIGEST===)
3. 审核摘要长图要点 (===HIGHLIGHTS===)
4. 深度美化排版图文 (===ARTICLE===)

注意：在 HTML 正文最开头嵌入封面图：
<div style="margin-bottom: 24px; text-align: center;">
    <img src="{cover_image_url}" style="width: 100%; border-radius: 10px; display: block; box-shadow: 0 4px 14px rgba(0,0,0,0.08);" alt="AI科技前沿" />
</div>

请严格遵循分隔规范输出：
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

    # 严格构建降级备选队列：3.8 始终第一，3.6 始终第二
    candidate_queue = []
    if model_name in available_models:
        candidate_queue.append(model_name)
    else:
        for m in available_models:
            if "3.8" in m and m not in candidate_queue:
                candidate_queue.append(m)
        if model_name not in candidate_queue:
            candidate_queue.append(model_name)

    for m in available_models:
        if "3.6" in m and m not in candidate_queue:
            candidate_queue.append(m)
    if "gemini-3.6-flash" not in candidate_queue:
        candidate_queue.append("gemini-3.6-flash")

    for m in available_models:
        if m not in candidate_queue:
            candidate_queue.append(m)

    print(f"🚦 最终降级执行链（仅限 3.x）: {' ➔ '.join(candidate_queue)}")

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
                    
                    # 默认值
                    title = f"AI 大模型前沿观察 | {today_str}"
                    digest = "一文纵览过去 24 小时全球大模型商业演进、新架构突破与行业核心风向。"
                    highlights = []
                    article_html = full_text

                    # 解析 TITLE
                    if "===TITLE===" in full_text:
                        part_after_title = full_text.split("===TITLE===")[1]
                        title_line = part_after_title.split("\n")[0].strip()
                        if title_line:
                            title = title_line

                    # 解析 DIGEST
                    if "===DIGEST===" in full_text:
                        part_after_digest = full_text.split("===DIGEST===")[1]
                        digest_line = part_after_digest.split("\n")[0].strip()
                        if digest_line:
                            digest = digest_line

                    # 解析 HIGHLIGHTS 与 ARTICLE
                    if "===HIGHLIGHTS===" in full_text and "===ARTICLE===" in full_text:
                        hl_text = full_text.split("===HIGHLIGHTS===")[1].split("===ARTICLE===")[0].strip()
                        article_html = full_text.split("===ARTICLE===")[1].strip()
                        for line in hl_text.split("\n"):
                            line = line.strip()
                            if line:
                                clean_line = re.sub(r'^\d+[\.、\s\-]+', '', line).strip()
                                if clean_line:
                                    highlights.append(clean_line)
                    elif "===ARTICLE===" in full_text:
                        article_html = full_text.split("===ARTICLE===")[1].strip()

                    if not highlights:
                        highlights = [
                            "全球主流大模型最新版本密集迭代，多模态推理能力显著提升",
                            "开源社区大模型活跃度再创新高，开发者工具链加速演进",
                            "AI 算力与商业化落地进入深水区，头部企业商业模式逐步成型"
                        ]

                    if article_html.startswith("```html"):
                        article_html = article_html[7:]
                    if article_html.startswith("```"):
                        article_html = article_html[3:]
                    if article_html.endswith("```"):
                        article_html = article_html[:-3]
                    
                    article_html = clean_wechat_html(article_html.strip())
                    print(f"🎉 模型 [{m}] 生成成功！标题: 《{title}》")
                    return title, digest, article_html, highlights

                elif response.status_code in (503, 429):
                    last_error = f"HTTP {response.status_code}: {response.text}"
                    print(f"⏳ 模型 [{m}] 临时高峰 (HTTP {response.status_code})，等待 {attempt * 4} 秒后重试...")
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
