import os
import requests

def build_preview_page(article_html: str, output_path: str = "index.html", has_summary_img: bool = True) -> str:
    """生成带有『审核摘要图』与『一键复制微信排版』的 Web 预览页面"""
    summary_img_block = ""
    if has_summary_img:
        summary_img_block = """
        <div style="margin-bottom: 30px; text-align: center; background: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
            <div style="font-weight: 600; font-size: 17px; margin-bottom: 12px; color: #2d3748; display: flex; align-items: center; justify-content: center; gap: 8px;">
                <span>🖼️ 今日大模型早报 · 审核速览摘要图</span>
            </div>
            <p style="font-size: 13px; color: #718096; margin-top: 0; margin-bottom: 16px;">
                可作为朋友圈、社群分发图或文章导读长图使用
            </p>
            <a href="summary.png" target="_blank" title="点击查看大图">
                <img src="summary.png" style="max-width: 100%; height: auto; border-radius: 10px; box-shadow: 0 4px 14px rgba(0,0,0,0.08); border: 1px solid #edf2f7;" alt="今日早报速览摘要图" />
            </a>
            <div style="margin-top: 12px;">
                <a href="summary.png" download="summary.png" style="display: inline-block; background: #ebf8ff; color: #2b6cb0; text-decoration: none; padding: 6px 14px; font-size: 13px; border-radius: 6px; font-weight: 500;">
                    ⬇️ 下载原尺寸摘要图
                </a>
            </div>
        </div>
        """

    template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI大模型前沿观察 · 微信发布与审核预览</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background-color: #eef2f6;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }}
        .top-bar {{
            position: sticky;
            top: 0;
            z-index: 999;
            background: #ffffff;
            box-shadow: 0 2px 10px rgba(0,0,0,0.06);
            padding: 14px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .title {{
            font-weight: 600;
            color: #1a202c;
            font-size: 16px;
        }}
        .btn-group {{
            display: flex;
            gap: 10px;
        }}
        .copy-btn {{
            background: #07c160;
            color: white;
            border: none;
            padding: 10px 22px;
            font-size: 15px;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 2px 6px rgba(7, 193, 96, 0.3);
        }}
        .copy-btn:hover {{
            background: #06ad56;
            transform: translateY(-1px);
        }}
        .container {{
            max-width: 720px;
            margin: 30px auto;
        }}
        .article-card {{
            background: #ffffff;
            padding: 30px 25px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        }}
        .toast {{
            position: fixed;
            top: 70px;
            left: 50%;
            transform: translateX(-50%);
            background: #333;
            color: #fff;
            padding: 10px 20px;
            border-radius: 20px;
            display: none;
            font-size: 14px;
            z-index: 1000;
        }}
    </style>
</head>
<body>
    <div class="top-bar">
        <div class="title">🤖 每日大模型图文与摘要审核台</div>
        <div class="btn-group">
            <button class="copy-btn" onclick="copyWechatRichText()">📋 一键复制微信排版</button>
        </div>
    </div>

    <div id="toast" class="toast">✅ 复制成功！去微信后台 Ctrl + V 粘贴即可！</div>

    <div class="container">
        <!-- 审核摘要图模块 -->
        {summary_img_block}

        <!-- 微信文章主体内容 -->
        <div class="article-card">
            <div id="wechat-content">
{article_html}
            </div>
        </div>
    </div>

    <script>
        async function copyWechatRichText() {{
            const content = document.getElementById('wechat-content');
            const html = content.innerHTML;
            const text = content.innerText;
            
            try {{
                const blobHtml = new Blob([html], {{ type: 'text/html' }});
                const blobText = new Blob([text], {{ type: 'text/plain' }});
                const data = [new ClipboardItem({{ 'text/html': blobHtml, 'text/plain': blobText }})];
                await navigator.clipboard.write(data);
                
                const toast = document.getElementById('toast');
                toast.style.display = 'block';
                setTimeout(() => {{ toast.style.display = 'none'; }}, 3000);
            }} catch (err) {{
                const range = document.createRange();
                range.selectNode(content);
                const selection = window.getSelection();
                selection.removeAllRanges();
                selection.addRange(range);
                document.execCommand('copy');
                selection.removeAllRanges();
                alert('已复制到剪贴板！');
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
