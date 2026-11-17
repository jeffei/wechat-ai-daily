import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from openrouter import generate_easter_egg_html, inject_easter_egg, fetch_openrouter_free_models
from builder import normalize_section_headings

class OpenRouterEasterEggTests(unittest.TestCase):
    def test_generate_easter_egg_html(self):
        mock_models = [
            {"name": "Nemotron 3 Ultra (free)", "tokens_wk": "3.2T", "context": "1M"},
            {"name": "Nemotron 3.5 Super VL (free)", "tokens_wk": "3.0T", "context": "1M"}
        ]
        html = generate_easter_egg_html(mock_models)
        self.assertIn("Nemotron 3 Ultra (free)", html)
        self.assertIn("Nemotron 3.5 Super VL (free)", html)
        self.assertIn("3.2T", html)
        self.assertIn("3.0T", html)
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
            {"name": "Nemotron 3 Ultra (free)", "tokens_wk": "3.2T", "context": "1M"}
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

    @patch("openrouter.requests.get")
    def test_fetch_openrouter_free_models_parsing(self, mock_get):
        mock_html = """
        <div>
            <h2>Free models</h2>
            <table>
                <tbody>
                    <tr>
                        <td>1</td>
                        <td><span>Model A (free)</span></td>
                        <td>5.0T</td>
                        <td>128k</td>
                    </tr>
                    <tr>
                        <td>2</td>
                        <td><span>Model B (free)</span></td>
                        <td>2.5T</td>
                        <td>1M</td>
                    </tr>
                </tbody>
            </table>
        </div>
        """
        mock_resp = Mock(status_code=200, text=mock_html)
        mock_get.return_value = mock_resp

        models = fetch_openrouter_free_models(top_n=2)
        self.assertEqual(len(models), 2)
        self.assertEqual(models[0]["name"], "Model A (free)")
        self.assertEqual(models[0]["tokens_wk"], "5.0T")
        self.assertEqual(models[0]["context"], "128k")
        self.assertEqual(models[1]["name"], "Model B (free)")

    @patch("openrouter.requests.get")
    def test_fetch_openrouter_free_models_fallback(self, mock_get):
        mock_get.side_effect = Exception("Network timeout")
        models = fetch_openrouter_free_models(top_n=2)
        self.assertEqual(len(models), 2)
        self.assertIn("Nemotron", models[0]["name"])


if __name__ == "__main__":
    unittest.main()
