"""固定微信正文模板：所有样式、栏目和图片由代码控制，内容只作为文本填充。"""

from html import escape

COVER_IMAGE_URL = "https://jeffei.github.io/wechat-ai-daily/assets/cover.jpg"
CATEGORIES = {
    "focus": "焦点头条 · 深度解读",
    "industry": "大厂与开源风云",
    "business": "前沿落地与商业观察",
}

ARTICLE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "title": {"type": "STRING"},
        "digest": {"type": "STRING"},
        "highlights": {"type": "ARRAY", "items": {"type": "STRING"}},
        "trend": {"type": "STRING"},
        "news": {"type": "ARRAY", "items": {
            "type": "OBJECT",
            "properties": {
                "category": {"type": "STRING", "enum": list(CATEGORIES)},
                "title": {"type": "STRING"},
                "paragraphs": {"type": "ARRAY", "items": {"type": "STRING"}},
                "analysis": {"type": "STRING"},
                "source": {"type": "STRING"},
            },
            "required": ["category", "title", "paragraphs", "analysis", "source"],
        }},
        "commentary": {"type": "ARRAY", "items": {"type": "STRING"}},
    },
    "required": ["title", "digest", "highlights", "trend", "news", "commentary"],
}


def validate_article(data: dict) -> dict:
    """拒绝缺失字段和错误类型，避免将失败响应或虚构默认内容发布出去。"""
    def check(value, schema, path):
        kind = schema["type"]
        if kind == "OBJECT":
            if not isinstance(value, dict):
                raise ValueError(f"{path} 必须是对象")
            if set(value) != set(schema["properties"]):
                raise ValueError(f"{path} 字段不符合内容协议")
            for key, child in schema["properties"].items():
                check(value[key], child, f"{path}.{key}")
        elif kind == "ARRAY":
            if not isinstance(value, list) or not value:
                raise ValueError(f"{path} 必须是非空列表")
            for i, item in enumerate(value):
                check(item, schema["items"], f"{path}[{i}]")
        elif not isinstance(value, str) or not value.strip():
            raise ValueError(f"{path} 必须是非空文本")
        elif "enum" in schema and value not in schema["enum"]:
            raise ValueError(f"{path} 包含未知栏目")

    check(data, ARTICLE_SCHEMA, "article")
    if not 3 <= len(data["highlights"]) <= 4:
        raise ValueError("highlights 必须包含 3~4 条看点")
    return data


def _text(value: str) -> str:
    return escape(value.strip(), quote=True)


def _paragraph(value: str, color: str = "#334155") -> str:
    return (f'<p style="margin: 0 0 14px; font-size: 15px; line-height: 1.9; '
            f'color: {color}; text-align: left; text-indent: 0;">{_text(value)}</p>')


def _heading(number: str, label: str) -> str:
    return (f'<section style="margin: 30px 0 16px; border-bottom: 1px solid #dbe5ef; '
            f'padding: 0 0 12px; text-align: left; text-indent: 0;">'
            f'<span style="font-size: 12px; color: #087e8b; font-weight: bold;">{number} / </span>'
            f'<span style="font-size: 18px; color: #10243a; font-weight: bold;">{label}</span></section>')


def render_article(data: dict, issue_date: str) -> str:
    """只接收经过校验的数据；不接受模型生成的 HTML、CSS 或图片地址。"""
    validate_article(data)
    parts = [
        '<section data-template="ai-daily-v1" style="font-family: -apple-system, BlinkMacSystemFont, '
        "'PingFang SC', 'Microsoft YaHei', sans-serif; background-color: #ffffff; "
        'color: #334155; font-size: 15px; line-height: 1.9; letter-spacing: 0.4px; '
        'text-align: left; text-indent: 0; overflow-wrap: anywhere; word-break: break-word;">',
        '<section style="background-color: #0b182b; border-top: 4px solid #22d3ee; padding: 24px 20px;">',
        '<p style="margin: 0 0 14px; color: #67e8f9; font-size: 11px; letter-spacing: 2px;">AI DAILY / INTELLIGENCE BRIEF</p>',
        '<p style="margin: 0 0 12px; color: #ffffff; font-size: 28px; font-weight: bold; line-height: 1.4;">大模型前沿观察</p>',
        f'<p style="margin: 0; color: #a5b8d0; font-size: 12px;">{_text(issue_date)} · 全球 AI 情报精选</p></section>',
        f'<img src="{COVER_IMAGE_URL}" alt="AI 科技前沿" style="display: block; width: 100%; height: auto; margin: 0 0 24px;"/>',
        '<section style="background-color: #eff8fc; border-left: 3px solid #0891b2; padding: 18px 16px; margin: 0 0 24px;">',
        '<p style="margin: 0 0 10px; color: #087e8b; font-size: 12px; font-weight: bold;">SIGNAL / 今日风向标</p>',
        _paragraph(data["trend"]), '</section>',
    ]
    for index, (category, label) in enumerate(CATEGORIES.items(), 1):
        parts.append(_heading(f"0{index}", label))
        items = [item for item in data["news"] if item["category"] == category]
        if not items:
            parts.append(_paragraph("本期暂无该栏目资讯。", "#64748b"))
        for number, item in enumerate(items, 1):
            parts.extend([
                '<section style="background-color: #f5f8fc; border-left: 3px solid #2563eb; padding: 18px 16px; margin: 0 0 18px; border-radius: 0 8px 8px 0;">',
                f'<p style="margin: 0 0 10px; color: #2563eb; font-size: 11px; font-weight: bold;">BRIEF {index:02d}.{number:02d}</p>',
                f'<h3 style="margin: 0 0 14px; color: #10243a; font-size: 18px; line-height: 1.6; text-align: left;">{_text(item["title"])}</h3>',
                *[_paragraph(p) for p in item["paragraphs"]],
                '<section style="border-top: 1px solid #dbe5ef; padding-top: 12px;">',
                '<p style="margin: 0 0 6px; color: #087e8b; font-size: 12px; font-weight: bold;">影响解读</p>',
                _paragraph(item["analysis"]), '</section>',
                f'<p style="margin: 0; color: #64748b; font-size: 11px; line-height: 1.7;">信息来源：{_text(item["source"])}</p>',
                '</section>',
            ])
    parts.extend([
        _heading("04", "主编锐评"),
        '<section style="background-color: #0b182b; border-top: 3px solid #22d3ee; padding: 22px 18px; border-radius: 0 0 8px 8px;">',
        '<p style="margin: 0 0 14px; color: #67e8f9; font-size: 11px; letter-spacing: 2px;">EDITOR’S PERSPECTIVE</p>',
        *[_paragraph(p, "#e2e8f0") for p in data["commentary"]], '</section>',
        '<p style="margin: 26px 0 0; padding-top: 14px; border-top: 1px solid #dbe5ef; color: #64748b; font-size: 10px; letter-spacing: 1px; text-align: center;">AI DAILY · 持续观察技术与商业的下一步</p>',
        '</section>',
    ])
    return "".join(parts)
