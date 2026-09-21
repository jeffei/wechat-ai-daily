import os
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from typing import List

def get_chinese_font(size: int):
    """跨平台获取中文字体"""
    candidate_fonts = [
        # Linux (Ubuntu GitHub Actions 安装 wqy-microhei 后路径)
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        # Windows 本地
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyh.ttf",
        "C:/Windows/Fonts/simhei.ttf",
        # macOS
        "/System/Library/Fonts/PingFang.ttc",
        "/Library/Fonts/Arial Unicode.ttf"
    ]
    for font_path in candidate_fonts:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                continue
    # 兜底默认字体
    return ImageFont.load_default()

def wrap_text(text: str, font, max_width: int, draw: ImageDraw.ImageDraw) -> List[str]:
    """根据像素宽度自动对中文文本进行折行"""
    lines = []
    current_line = ""
    for char in text:
        test_line = current_line + char
        # 获取文字渲染宽度
        bbox = draw.textbbox((0, 0), test_line, font=font)
        width = bbox[2] - bbox[0]
        if width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = char
    if current_line:
        lines.append(current_line)
    return lines

def generate_summary_card(highlights: List[str], output_path: str = "summary.png") -> str:
    """
    生成高颜值的每日 AI 大模型资讯摘要卡片图 (800px 宽)
    """
    width = 800
    padding = 40
    card_width = width - padding * 2

    # 准备字体
    font_title = get_chinese_font(32)
    font_subtitle = get_chinese_font(18)
    font_badge = get_chinese_font(16)
    font_bullet_title = get_chinese_font(20)
    font_bullet_body = get_chinese_font(17)
    font_footer = get_chinese_font(15)

    # 预计算卡片高度
    # 临时画布用于测量文本尺寸
    temp_img = Image.new("RGB", (width, 200))
    temp_draw = ImageDraw.Draw(temp_img)

    today_str = datetime.now().strftime("%Y年%m月%d日")
    
    # 测量每个亮点卡片的高度
    content_blocks = []
    total_content_height = 0
    for idx, item in enumerate(highlights, 1):
        lines = wrap_text(item, font_bullet_body, card_width - 50, temp_draw)
        block_h = 35 + len(lines) * 28 + 20
        content_blocks.append((f"0{idx}" if idx < 10 else str(idx), lines, block_h))
        total_content_height += block_h + 15

    header_height = 170
    footer_height = 80
    total_height = header_height + total_content_height + footer_height + 30

    # 创建主画布（浅灰高级底色）
    img = Image.new("RGB", (width, total_height), "#f4f6f9")
    draw = ImageDraw.Draw(img)

    # 1. 顶部 Header 渐变质感背景 (科技深蓝底色卡片)
    draw.rounded_rectangle(
        [(padding, 30), (width - padding, header_height)],
        radius=14,
        fill="#1a365d"
    )

    # 顶部标签
    draw.text((padding + 25, 52), "⚡ DAILY AI INSIGHT", font=font_badge, fill="#63b3ed")
    # 顶层主标题
    draw.text((padding + 25, 80), "AI 大模型科技前沿 · 每日速报", font=font_title, fill="#ffffff")
    # 副标题与日期
    draw.text((padding + 25, 126), f"📅 {today_str} · 全球大模型重磅动态与行业风向", font=font_subtitle, fill="#cbd5e0")

    # 2. 依次渲染每个核心要点卡片 (白色圆角卡片，带左侧微重音)
    cur_y = header_height + 25
    for num_str, lines, block_h in content_blocks:
        card_box = [(padding, cur_y), (width - padding, cur_y + block_h)]
        # 白色卡片背景
        draw.rounded_rectangle(card_box, radius=10, fill="#ffffff", outline="#e2e8f0", width=1)
        # 左侧装饰条 (科技蓝)
        draw.rounded_rectangle([(padding, cur_y), (padding + 6, cur_y + block_h)], radius=3, fill="#3182ce")

        # 序号 Badge
        draw.rounded_rectangle(
            [(padding + 20, cur_y + 16), (padding + 52, cur_y + 40)],
            radius=6,
            fill="#ebf8ff"
        )
        draw.text((padding + 25, cur_y + 18), f"#{num_str}", font=font_badge, fill="#2b6cb0")

        # 内容文本逐行渲染
        line_y = cur_y + 48
        for line in lines:
            draw.text((padding + 24, line_y), line, font=font_bullet_body, fill="#2d3748")
            line_y += 28

        cur_y += block_h + 15

    # 3. 底部 Footer 审核水印与提示
    footer_text = "🤖 本期图文已就绪 · 由 Google Gemini 自动化分析生成 · 供审核确认"
    draw.text((padding + 10, total_height - 50), footer_text, font=font_footer, fill="#718096")

    # 确保输出目录存在
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    img.save(output_path, "PNG", quality=95)
    print(f"✅ 摘要图已成功生成至: {output_path}")
    return output_path
