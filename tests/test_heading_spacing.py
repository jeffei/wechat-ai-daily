import sys
import tempfile
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from builder import build_preview_page, normalize_section_headings


class HeadingSpacingTests(unittest.TestCase):
    def test_entities_nested_markup_and_body_are_preserved(self):
        html = '''<section><section style="display: table; padding: 6px 14px; text-indent: 2em">
          <span>&nbsp;&#xA0;　<strong>🔥 焦点头条 · 深度解读</strong>　</span>
        </section><p>OpenAI API keeps normal spaces &amp; symbols.</p></section>'''
        soup = BeautifulSoup(normalize_section_headings(html), "html.parser")
        heading = soup.section.section
        self.assertEqual(heading.get_text(), "🔥 焦点头条 · 深度解读")
        self.assertIsNotNone(heading.strong)
        self.assertIn("padding: 6px 8px", heading["style"])
        self.assertNotIn("2em", heading["style"])
        self.assertEqual(soup.p.get_text(), "OpenAI API keeps normal spaces & symbols.")

    def test_does_not_restyle_body_card_or_unrelated_heading(self):
        html = '<div style="padding:20px"><h2>今日风向标</h2><p>大厂与开源风云值得持续关注。</p></div><h2>Other heading</h2>'
        soup = BeautifulSoup(normalize_section_headings(html), "html.parser")
        self.assertEqual(soup.div["style"], "padding:20px")
        self.assertNotIn("style", soup.p.attrs)
        self.assertNotIn("style", soup.find_all("h2")[1].attrs)

    def test_preview_and_repeated_normalization(self):
        html = '<section style="display: table"><span>\n   ⚡ 大厂与开源风云  \n</span></section>'
        cleaned = normalize_section_headings(html)
        self.assertEqual(normalize_section_headings(cleaned), cleaned)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "index.html"
            build_preview_page(html, output_path=str(path), has_summary_img=False)
            soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
            self.assertEqual(soup.select_one("#wechat-content section").get_text(), "⚡ 大厂与开源风云")


if __name__ == "__main__":
    unittest.main()
