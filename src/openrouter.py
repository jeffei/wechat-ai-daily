import re
import requests
from typing import List, Dict

DISCOVER_URL = "https://openrouter.ai/discover"

def fetch_openrouter_free_models(top_n: int = 2) -> List[Dict]:
    """
    抓取 OpenRouter Discover (https://openrouter.ai/discover) 中的 Free models 免费模型列表，
    获取全网调用量与热度最高的免费模型名称、每周 Token 跑量及上下文大小。
    """
    models = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    try:
        resp = requests.get(DISCOVER_URL, headers=headers, timeout=12)
        if resp.status_code == 200:
            html = resp.text
            idx = html.find("Free models</h2>")
            if idx != -1:
                end_idx = html.find("</tbody>", idx)
                section_html = html[idx:end_idx]
                rows = section_html.split('<tr class="or-table__row group cursor-pointer">')[1:]
                for row in rows:
                    name_match = re.search(r'font-semibold">([^<]+)</span>', row)
                    vals = re.findall(r'tabular-nums font-medium text-foreground">([^<]+)</span>', row)
                    if name_match and len(vals) >= 2:
                        models.append({
                            "name": name_match.group(1).strip(),
                            "tokens_wk": vals[0].strip(),
                            "context": vals[1].strip()
                        })
    except Exception as e:
        print(f"⚠️ 抓取 OpenRouter Discover 免费模型失败: {e}")

    # 若页面改版或网络波动未抓到数据，使用保底的高热度免费模型数据
    if not models:
        models = [
            {"name": "Space Bunny Alpha", "tokens_wk": "23.4T", "context": "1M"},
            {"name": "Nemotron 3 Ultra (free)", "tokens_wk": "5.9T", "context": "1M"}
        ]
        
    return models[:top_n]


def generate_easter_egg_html(models: List[Dict]) -> str:
    """
    生成微信排版兼容的【极客彩蛋 · OpenRouter 免费大模型福利】卡片
    采用微信原生支持的内联 CSS，避免样式冲突或全宽拉伸
    """
    items_html = []
    for idx, m in enumerate(models, 1):
        name = m.get("name", "Unknown Model")
        tokens_wk = m.get("tokens_wk", "--")
        context = m.get("context", "--")
        
        item_card = f"""
<div style="background-color: #ffffff; border: 1px solid #fde68a; border-radius: 8px; padding: 14px 16px; margin-bottom: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
    <div style="font-size: 15px; font-weight: bold; color: #1f2937; margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between;">
        <span>🚀 {idx}. {name}</span>
        <span style="background-color: #dcfce7; color: #15803d; font-size: 12px; font-weight: bold; padding: 2px 8px; border-radius: 12px;">免费 (Free)</span>
    </div>
    <div style="font-size: 13px; color: #4b5563; line-height: 1.7;">
        <div style="margin-bottom: 4px;">📊 <b>每周 Token 跑量：</b><span style="color: #d97706; font-weight: bold; font-size: 14px;">{tokens_wk}</span> Tokens/wk</div>
        <div>🧠 <b>上下文窗口：</b><span style="color: #374151; font-weight: 500;">{context}</span></div>
    </div>
</div>"""
        items_html.append(item_card.strip())
        
    cards_str = "\n".join(items_html)
    
    html = f"""<!-- 🎁 彩蛋 · OpenRouter 免费大模型福利 -->
<section style="display: table; text-indent: 0; margin: 32px 0 14px 0; background-color: #fef3c7; border-radius: 6px; padding: 6px 14px; text-align: left;">
    <span style="color: #b45309; font-size: 15px; font-weight: bold; letter-spacing: 0.5px; text-indent: 0; line-height: 1.2;">
        🎁 彩蛋 · OpenRouter 免费大模型福利
    </span>
</section>
<div style="background-color: #fffbeb; border-left: 4px solid #f59e0b; border-radius: 8px; padding: 18px 20px; margin-bottom: 22px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
    <p style="margin: 0 0 14px 0; font-size: 14px; line-height: 1.8; color: #78350f; text-align: justify;">
        【专属福利】来自 <b>OpenRouter Discover</b> 实时全网热度最高的 2 款<b>免费大模型</b>！附带每周全网 Token 跑量与上下文规格，送给需要调试与开发的朋友：
    </p>
    {cards_str}
</div>"""
    return html.strip()


def inject_easter_egg(article_html: str, easter_egg_html: str) -> str:
    """
    将彩蛋模块嵌入在推文末尾（主编锐评之后，外层容器闭合之前）
    """
    # 清理可能混入的 ===END=== 等模型结尾标记
    article_html = re.sub(r'===\s*END(?:[_\s]*ARTICLE)?\s*===.*$', '', article_html, flags=re.IGNORECASE | re.DOTALL).strip()
    last_section_idx = article_html.rfind("</section>")
    if last_section_idx != -1:
        return article_html[:last_section_idx] + "\n" + easter_egg_html + "\n</section>"
    return article_html + "\n" + easter_egg_html


if __name__ == "__main__":
    print("Testing OpenRouter Free Models Fetcher...")
    top_models = fetch_openrouter_free_models(top_n=2)
    print(f"Fetched {len(top_models)} models:")
    for m in top_models:
        print(f" - {m['name']} | {m['tokens_wk']} | {m['context']}")
    rendered = generate_easter_egg_html(top_models)
    print("Rendered HTML length:", len(rendered))

