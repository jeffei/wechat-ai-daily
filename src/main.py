import os
import sys
import shutil
import re
from datetime import datetime

# 保证模块导入路径正确
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fetcher import aggregate_news
from writer import generate_wechat_article
from image_generator import generate_summary_card
from builder import build_preview_page, notify_user

DOCS_DIR = "docs"

def clean_old_history(docs_dir: str, keep_count: int = 5):
    """只保留 docs 目录下最新的 keep_count 个时间戳执行文件夹，删除多余的旧文件夹"""
    if not os.path.exists(docs_dir):
        return

    # 匹配时间戳命名的子文件夹，例如 2026-09-21_10-00-00
    timestamp_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}(-\d{2})?$')
    subfolders = []
    
    for item in os.listdir(docs_dir):
        full_path = os.path.join(docs_dir, item)
        if os.path.isdir(full_path) and timestamp_pattern.match(item):
            subfolders.append((item, full_path))

    # 按文件夹名称字典序排序（ISO 日期格式自然正序）
    subfolders.sort(key=lambda x: x[0])

    # 如果超过保留数量，从最旧的开始删除
    if len(subfolders) > keep_count:
        to_delete = subfolders[:len(subfolders) - keep_count]
        for name, folder_path in to_delete:
            print(f"🗑️ 正在清理更早的历史归档文件夹: {folder_path} ...")
            shutil.rmtree(folder_path, ignore_errors=True)
        print(f"✅ 历史归档已整理，当前仅保留最新的 {keep_count} 个版本。")

def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ 错误：未检测到 GEMINI_API_KEY 环境变量！请确保在 GitHub Settings -> Secrets 中添加了 GEMINI_API_KEY。")
        sys.exit(1)

    # 1. 抓取全球大模型资讯
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚀 开始执行大模型科技新闻采集...")
    news_content = aggregate_news()
    print(f"✅ 资讯采集完成，共收集素材约 {len(news_content)} 字符。")
    
    # 2. 调用 Gemini 3.x 生成微信图文与速览摘要
    print("🤖 正在调用 Google Gemini 3.x 生成微信图文、爆款标题与速览摘要...")
    title, digest, article_html, highlights = generate_wechat_article(news_content)
    print(f"✅ Gemini 生成成功！\n📌 推荐标题: 《{title}》\n📝 推荐摘要: {digest}")

    # 3. 按当前执行时间创建专属历史归档文件夹 (格式: 2026-09-22_10-00-00)
    exec_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archive_dir = os.path.join(DOCS_DIR, exec_timestamp)
    os.makedirs(archive_dir, exist_ok=True)
    print(f"📁 已创建本次执行归档目录: {archive_dir}")

    # 4. 生成【审核摘要图】并存放在本次目录中
    img_archive_path = os.path.join(archive_dir, "summary.png")
    generate_summary_card(highlights, output_path=img_archive_path)

    # 5. 生成本次归档的 index.html
    html_archive_path = os.path.join(archive_dir, "index.html")
    build_preview_page(
        article_html=article_html,
        title=title,
        digest=digest,
        output_path=html_archive_path,
        has_summary_img=True
    )

    # 6. 同时将最新版本同步复制到 docs/ 根目录（便于 GitHub Pages 首页直接打开最新一期）
    latest_html_path = os.path.join(DOCS_DIR, "index.html")
    latest_img_path = os.path.join(DOCS_DIR, "summary.png")
    shutil.copy2(html_archive_path, latest_html_path)
    shutil.copy2(img_archive_path, latest_img_path)
    # 项目根目录也存一份作为镜像
    shutil.copy2(html_archive_path, "index.html")
    shutil.copy2(img_archive_path, "summary.png")
    print(f"✅ 最新网页与摘要图已就绪: {latest_html_path} & {latest_img_path}")

    # 7. 严格执行归档保留策略：仅保留最新的 5 个历史归档文件夹
    clean_old_history(DOCS_DIR, keep_count=5)

    # 8. 发送微信推送通知
    today = datetime.now().strftime('%m月%d日 %H:%M')
    notify_user(
        title=f"📢 今日大模型早报与摘要图已就绪（{today}）",
        message="今日《大模型科技观察》及速览审核长图已由 Gemini 3.x 生成完毕！点击链接即可查看摘要图并一键复制排版发布。"
    )
    print("🎉 任务全部圆满完成！")

if __name__ == "__main__":
    main()
