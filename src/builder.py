import os
import requests

def build_preview_page(
    article_html: str,
    title: str = "AI 大模型前沿科技观察",
    digest: str = "近期全球大模型商业与技术核心风向速览。",
    output_path: str = "index.html",
    has_summary_img: bool = True
) -> str:
    """生成带有『标题复制』、『摘要复制』、『审核图』与『一键复制微信正文』的发布工作台"""
    
    summary_img_block = ""
    if has_summary_img:
        summary_img_block = """
        <div style="margin-bottom: 24px; background: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.04); text-align: center;">
            <div style="font-weight: 600; font-size: 16px; margin-bottom: 8px; color: #2d3748;">
                🖼️ 今日审核速览摘要长图（已自动渲染）
            </div>
            <p style="font-size: 13px; color: #718096; margin-top: 0; margin-bottom: 14px;">
                审核确认今日核心要点，可长按/右键保存直接发朋友圈、社群
            </p>
            <a href="summary.png" target="_blank" title="点击查看大图">
                <img src="summary.png" style="max-width: 100%; height: auto; border-radius: 10px; box-shadow: 0 4px 14px rgba(0,0,0,0.08); border: 1px solid #edf2f7;" alt="今日早报速览摘要图" />
            </a>
            <div style="margin-top: 12px;">
                <a href="summary.png" download="summary.png" style="display: inline-block; background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; text-decoration: none; padding: 7px 16px; font-size: 13px; border-radius: 6px; font-weight: 600;">
                    ⬇️ 下载原尺寸摘要海报
                </a>
            </div>
        </div>
        """

    template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} · 微信公众号发布工作台</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background-color: #f0f3f8;
            font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
            color: #2d3748;
        }}
        .top-bar {{
            position: sticky;
            top: 0;
            z-index: 999;
            background: #ffffff;
            box-shadow: 0 2px 10px rgba(0,0,0,0.06);
            padding: 12px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .brand {{
            font-weight: 700;
            color: #1a202c;
            font-size: 16px;
        }}
        .copy-main-btn {{
            background: #07c160;
            color: white;
            border: none;
            padding: 11px 24px;
            font-size: 15px;
            font-weight: bold;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 2px 8px rgba(7, 193, 96, 0.35);
        }}
        .copy-main-btn:hover {{
            background: #06ad56;
            transform: translateY(-1px);
        }}
        .container {{
            max-width: 740px;
            margin: 24px auto;
            padding: 0 15px;
        }}
        /* 微信公众号发布辅助工作台卡片 */
        .helper-card {{
            background: #ffffff;
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 24px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.04);
            border-top: 4px solid #1a73e8;
        }}
        .helper-title {{
            font-size: 16px;
            font-weight: bold;
            color: #1a202c;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .helper-row {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
        }}
        .helper-label {{
            font-weight: 600;
            font-size: 13px;
            color: #4a5568;
            min-width: 75px;
        }}
        .helper-val {{
            font-size: 14px;
            color: #1a202c;
            flex-grow: 1;
            word-break: break-all;
            line-height: 1.5;
        }}
        .small-copy-btn {{
            background: #e8f0fe;
            color: #1a73e8;
            border: none;
            padding: 6px 14px;
            font-size: 12px;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.15s ease;
        }}
        .small-copy-btn:hover {{
            background: #d2e3fc;
        }}
        .article-card {{
            background: #ffffff;
            padding: 35px 28px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.04);
        }}
        .toast {{
            position: fixed;
            top: 75px;
            left: 50%;
            transform: translateX(-50%);
            background: #1a202c;
            color: #ffffff;
            padding: 11px 22px;
            border-radius: 25px;
            display: none;
            font-size: 14px;
            font-weight: 500;
            z-index: 1000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
    </style>
</head>
<body>
    <div class="top-bar">
        <div class="brand">🚀 微信公众号 · AI大模型早报发布台</div>
        <button class="copy-main-btn" onclick="copyArticleBody()">📋 一键复制正文排版</button>
    </div>

    <div id="toast" class="toast">✅ 已复制到剪贴板！</div>

    <div class="container">
        <!-- 微信发布助手（标题、摘要） -->
        <div class="helper-card">
            <div class="helper-title">🎯 微信后台一键发文助手</div>
            
            <div class="helper-row">
                <div class="helper-label">📌 推荐标题</div>
                <div class="helper-val" id="title-text">{title}</div>
                <button class="small-copy-btn" onclick="copyTextById('title-text', '文章标题已复制！')">复制标题</button>
            </div>

            <div class="helper-row">
                <div class="helper-label">📝 推荐摘要</div>
                <div class="helper-val" id="digest-text">{digest}</div>
                <button class="small-copy-btn" onclick="copyTextById('digest-text', '推文摘要已复制！')">复制摘要</button>
            </div>
            
            <div style="font-size: 12px; color: #718096; margin-top: 10px; display: flex; justify-content: space-between;">
                <span>💡 复制标题与摘要后，点击上方绿色按钮复制正文，在公众号后台 Ctrl+V 即可。</span>
            </div>
        </div>

        <!-- 审核速览长图 -->
        {summary_img_block}

        <!-- 微信正文区域 -->
        <div class="article-card">
            <div style="font-size: 13px; color: #a0aec0; margin-bottom: 16px; border-bottom: 1px dashed #e2e8f0; padding-bottom: 8px;">
                📖 微信排版效果实时预览区（已应用最舒适自媒体排版规范）
            </div>
            <div id="wechat-content">
{article_html}
            </div>
        </div>
    </div>

    <script>
        function showToast(msg) {{
            const toast = document.getElementById('toast');
            toast.innerText = msg;
            toast.style.display = 'block';
            setTimeout(() => {{ toast.style.display = 'none'; }}, 2500);
        }}

        async function copyTextById(elementId, successMsg) {{
            const text = document.getElementById(elementId).innerText.trim();
            try {{
                await navigator.clipboard.writeText(text);
                showToast("✅ " + successMsg);
            }} catch(e) {{
                const input = document.createElement('textarea');
                input.value = text;
                document.body.appendChild(input);
                input.select();
                document.execCommand('copy');
                document.body.removeChild(input);
                showToast("✅ " + successMsg);
            }}
        }}

        async function copyArticleBody() {{
            const content = document.getElementById('wechat-content');
            const html = content.innerHTML;
            const text = content.innerText;
            
            try {{
                const blobHtml = new Blob([html], {{ type: 'text/html' }});
                const blobText = new Blob([text], {{ type: 'text/plain' }});
                const data = [new ClipboardItem({{ 'text/html': blobHtml, 'text/plain': blobText }})];
                await navigator.clipboard.write(data);
                showToast('✅ 正文排版已复制！微信后台直接 Ctrl + V 粘贴即可！');
            }} catch (err) {{
                const range = document.createRange();
                range.selectNode(content);
                const selection = window.getSelection();
                selection.removeAllRanges();
                selection.addRange(range);
                document.execCommand('copy');
                selection.removeAllRanges();
                showToast('✅ 正文排版已复制到剪贴板！');
            }}
        }}
    </script>
</body>
</html>
"""
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(template)
    return output_path

def notify_user(title: str, message: str):
    serverchan_key = os.getenv("SERVERCHAN_KEY")
    if serverchan_key:
        try:
            requests.post(
                f"https://sctapi.ftqq.com/{serverchan_key}.send",
                data={"title": title, "desp": message},
                timeout=10
            )
            print("Server酱 通知已发出")
        except Exception as e:
            print(f"推送通知失败: {e}")
