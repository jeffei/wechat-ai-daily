import sys
import unittest
from pathlib import Path
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from openrouter import generate_easter_egg_html, inject_easter_egg
from builder import normalize_section_headings

class OpenRouterEasterEggTests(unittest.TestCase):
    def test_generate_easter_egg_html(self):
        mock_models = [
            {"name": "Space Bunny Alpha", "tokens_wk": "23.4T", "context": "1M"},
            {"name": "Nemotron 3 Ultra (free)", "tokens_wk": "5.9T", "context": "1M"}
        ]
        html = generate_easter_egg_html(mock_models)
        self.assertIn("Space Bunny Alpha", html)
        self.assertIn("Nemotron 3 Ultra (free)", html)
        self.assertIn("23.4T", html)
        self.assertIn("5.9T", html)
        self.assertIn("Tokens/wk", html)
        self.assertIn("display: table", html)
        self.assertIn("text-indent: 0", html)

    def test_inject_easter_egg(self):
        base_article = '<section style="font-size:15px;"><p>Content</p></section>'
        easter_egg = '<div id="easter-egg">Bonus Content</div>'
        result = inject_easter_egg(base_article, easter_egg)
        self.assertTrue(result.endswith("</section>"))
        self.assertIn('<div id="easter-egg">Bonus Content</div>', result)
        self.assertIn('<p>Content</p>', result)

    def test_heading_normalization_with_easter_egg(self):
        mock_models = [
            {"name": "Space Bunny Alpha", "tokens_wk": "23.4T", "context": "1M"}
        ]
        egg_html = generate_easter_egg_html(mock_models)
        cleaned = normalize_section_headings(egg_html)
        soup = BeautifulSoup(cleaned, "html.parser")
        heading = soup.find("section")
        self.assertIsNotNone(heading)
        self.assertEqual(heading.get_text().strip(), "🎁 彩蛋 · OpenRouter 免费大模型福利")
        self.assertIn("padding: 6px 8px", heading["style"])
        self.assertIn("text-indent: 0", heading["style"])

    def test_end_marker_is_stripped_cleanly(self):
        article_with_end = '<section style="font-size:15px;"><p>Content</p></section>\n===END==='
        easter_egg = '<div id="easter-egg">Bonus Content</div>'
        injected = inject_easter_egg(article_with_end, easter_egg)
        self.assertNotIn("===END===", injected)
        self.assertTrue(injected.endswith("</section>"))

        normalized = normalize_section_headings(injected + "\n===END===")
        self.assertNotIn("===END===", normalized)


if __name__ == "__main__":
    unittest.main()
