import os
from PIL import Image, ImageDraw, ImageFont, ImageOps
from datetime import datetime
from typing import List
from pathlib import Path

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
    """固定科技简报长图：紧凑呈现看点，并完整嵌入公众号品牌物料。"""
    width, padding = 800, 40
    card_width = width - padding * 2
    navy, cyan = "#0b182b", "#22d3ee"
    font_title = get_chinese_font(42)
    font_label = get_chinese_font(20)
    font_date = get_chinese_font(23)
    font_lead = get_chinese_font(27)
    font_body = get_chinese_font(24)

    # 从源文件位置定位，兼容本地和 GitHub Actions 的不同工作目录。
    brand_path = Path(__file__).resolve().parents[1] / "微信公众号二维码.png"
    with Image.open(brand_path) as source:
        brand = ImageOps.exif_transpose(source).convert("RGBA")
    brand_height = round(brand.height * card_width / brand.width)
    brand = brand.resize((card_width, brand_height), Image.Resampling.LANCZOS)

    measure = ImageDraw.Draw(Image.new("RGB", (width, 1)))
    blocks = []
    for index, item in enumerate(highlights):
        font = font_lead if index == 0 else font_body
        line_height = 43 if index == 0 else 38
        lines = wrap_text(item, font, card_width - 64, measure)
        block_height = 86 + len(lines) * line_height + 24
        blocks.append((lines, font, line_height, block_height))

    header_height = 250
    content_height = sum(block[3] + 20 for block in blocks)
    brand_y = header_height + content_height + 72
    total_height = brand_y + brand_height + 40
    img = Image.new("RGB", (width, total_height), navy)
    draw = ImageDraw.Draw(img)

    # 仅在顶部添加低对比度网格与电光青线条，正文区域保持干净。
    for x in range(480, width, 32):
        draw.line((x, 0, x, 215), fill="#142c43", width=1)
    for y in range(0, 216, 32):
        draw.line((480, y, width, y), fill="#142c43", width=1)
    draw.rectangle((padding, 34, padding + 42, 39), fill=cyan)
    draw.text((padding, 58), "AI DAILY / INTELLIGENCE BRIEF", font=font_label, fill=cyan)
    draw.text((padding - 2, 100), "大模型前沿 · 核心速览", font=font_title, fill="#ffffff")
    today_str = datetime.now().strftime("%Y.%m.%d")
    draw.text((padding, 180), today_str, font=font_date, fill="#b3c7db")
    edition = f"本期 {len(highlights):02d} 条精选"
    draw.text((width - padding - draw.textlength(edition, font=font_label), 183),
              edition, font=font_label, fill="#b3c7db")

    cur_y = header_height
    for index, (lines, font, line_height, block_height) in enumerate(blocks):
        lead = index == 0
        draw.rounded_rectangle((padding, cur_y, width - padding, cur_y + block_height),
                               radius=16, fill="#102f46" if lead else "#f3f7fb",
                               outline="#23718a" if lead else "#dce6ef", width=2)
        draw.rounded_rectangle((padding + 28, cur_y + 26, padding + 79, cur_y + 59),
                               radius=6, fill=cyan if lead else "#dbeaf4")
        draw.text((padding + 39, cur_y + 28), f"{index + 1:02d}", font=font_label,
                  fill=navy if lead else "#155e75")
        draw.text((padding + 94, cur_y + 28), "本期焦点 / FOCUS" if lead else "前沿简讯 / BRIEF",
                  font=font_label, fill="#67e8f9" if lead else "#247087")
        line_y = cur_y + 84
        for line in lines:
            draw.text((padding + 32, line_y), line, font=font,
                      fill="#f0f9ff" if lead else "#1e3449")
            line_y += line_height
        cur_y += block_height + 20

    # 公众号信息和新闻在同一张图片中；完整保留物料与二维码留白。
    draw.line((padding, cur_y + 12, width - padding, cur_y + 12), fill="#284156", width=1)
    draw.text((padding, cur_y + 30), "关注长安派 · 长按识别下方二维码", font=font_label, fill="#b3c7db")
    img.paste(brand, (padding, brand_y), brand)

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    img.save(output_path, "PNG")
    print(f"✅ 摘要图已成功生成至: {output_path}")
    return output_path
