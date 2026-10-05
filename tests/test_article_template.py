import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from template import render_article, validate_article
from writer import generate_wechat_article
from builder import build_preview_page


def example():
    return {
        "title": "固定模板演示｜AI 前沿观察",
        "digest": "本页仅用于展示固定模板的排版效果，内容为示例，不代表真实新闻。",
        "highlights": ["示例看点一", "示例看点二", "示例看点三"],
        "trend": "示例内容：从模型能力到产品体验，关注技术进步如何转化为实际价值。",
        "news": [{
            "category": category,
            "title": title,
            "paragraphs": ["这是一段排版演示内容，不代表真实新闻。标题、段落和卡片样式全部由固定模板控制。", "正文采用浅色背景、清晰字号与舒适行距，适合在手机上连续阅读。"],
            "analysis": "示例解读：观察实际应用效果，也关注成本、可靠性与用户体验。",
            "source": "模板演示，非真实新闻",
        } for category, title in [
            ("focus", "模型能力进阶，应用体验成为关注焦点"),
            ("industry", "从开源工具到开发生态，观察协作的价值"),
            ("business", "从技术验证到业务落地，关注可衡量的成果"),
        ]],
        "commentary": ["技术的价值最终要在真实使用中接受检验。以上内容仅用于模板演示。"],
    }


class TemplateTests(unittest.TestCase):
    def test_fixed_layout_and_escaped_content(self):
        data = example()
        data["news"][0]["title"] = '<script>alert("x")</script>'
        html = render_article(data, "2026年10月05日")
        soup = BeautifulSoup(html, "html.parser")
        self.assertIsNone(soup.script)
        self.assertEqual(soup.h3.text, data["news"][0]["title"])
        self.assertEqual(len(soup.find_all("img")), 1)
        self.assertNotIn("ai-leaders", html)
        self.assertFalse(soup.select("style, link, iframe"))
        self.assertEqual(html, render_article(data, "2026年10月05日"))

    def test_invalid_content_is_rejected(self):
        for key, value in [("news", []), ("trend", " "), ("commentary", "wrong"), ("highlights", ["one"])]:
            with self.subTest(key=key):
                data = example()
                data[key] = value
                with self.assertRaises(ValueError):
                    validate_article(data)
        data = example()
        data["news"][0]["category"] = "custom"
        with self.assertRaises(ValueError):
            validate_article(data)

    def test_preview_keeps_template_and_copy_controls(self):
        html = render_article(example(), "2026年10月05日")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "index.html"
            build_preview_page(html, title='<b>title</b>', digest='<img src=x>', output_path=str(path))
            page = path.read_text(encoding="utf-8")
            self.assertIn(html, page)
            self.assertIn("&lt;b&gt;title&lt;/b&gt;", page)
            self.assertIn("copyArticleBody", page)
            self.assertIn("copyTextById", page)
            self.assertIn('href="summary.png"', page)
            self.assertNotIn("ai-leaders", page)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
    @patch("writer.get_available_models", return_value=["gemini-3.8-flash"])
    @patch("writer.requests.post")
    @patch("time.sleep")
    def test_writer_retries_bad_json_and_preserves_return_contract(self, sleep, post, models):
        def response(text):
            return Mock(status_code=200, json=lambda: {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": text}]}}]})
        data = example()
        post.side_effect = [response("<section>invalid</section>"), response(json.dumps(data))]
        title, digest, html, highlights = generate_wechat_article("sample news")
        self.assertEqual((title, digest, highlights), (data["title"], data["digest"], data["highlights"]))
        self.assertIn('data-template="ai-daily-v1"', html)
        self.assertEqual(post.call_count, 2)
        self.assertEqual(post.call_args.kwargs["json"]["generationConfig"]["responseMimeType"], "application/json")


if __name__ == "__main__":
    unittest.main()
