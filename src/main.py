import os
import sys
from datetime import datetime
from fetcher import aggregate_news
from writer import generate_wechat_article
from builder import build_preview_page, notify_user

def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚀 开始执行大模型资讯抓取...")
    news_content = aggregate_news()
    print(f"✅ 资讯采集完成，共收集素材约 {len(news_content)} 字符。")
    
    print("🤖 正在调用 Google Gemini 生成微信图文与深度排版...")
    article_html = generate_wechat_article(news_content)
    print("✅ Gemini 文章生成与内联排版成功！")
    
    # 确保 docs 目录存在（方便 GitHub Pages 托管）
    os.makedirs("docs", exist_ok=True)
    build_preview_page(article_html, output_path="docs/index.html")
    # 同时在根目录存一份
    build_preview_page(article_html, output_path="index.html")
    print("✅ 已生成预览网页 index.html 及 docs/index.html！")
    
    # 发送推送通知提醒用户
    today = datetime.now().strftime('%m月%d日')
    notify_user(
        title=f"📢 今日大模型早报已就绪（{today}）",
        message="你的《大模型前沿早报》已由 Gemini 生成并排版完毕！点击 GitHub Pages 链接即可一键复制并发布到微信公众号。"
    )
    print("🎉 任务全部圆满完成！")

if __name__ == "__main__":
    main()
