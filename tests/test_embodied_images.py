import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from template import render_article, render_embodied_article, validate_article
from writer import generate_wechat_article, generate_embodied_article
from fetcher import extract_image_url, download_news_images
from main import clean_old_history


def example_embodied():
    return {
        "title": "具身智能前沿｜机器人新品",
        "digest": "本周多家机器人企业发布新型号硬件与灵巧手产品。",
        "highlights": ["新品机器人发布", "灵巧手精度提升", "产业融资突破"],
        "trend": "具身智能正在加速走向物理世界商业化落地。",
        "news": [
            {
                "category": "focus",
                "title": "某企业发布新款人形机器人，具备全身协同运动能力",
                "paragraphs": ["该企业本周正式发布了全新一代人形机器人硬件平台。"],
                "analysis": "这将显著降低二次开发门槛并加速场景验证。",
                "source": "IEEE Spectrum",
                "image_url": "https://example.com/robot_v2.jpg",
            },
            {
                "category": "industry",
                "title": "供应链核心部件成本持续下探",
                "paragraphs": ["关节模组与六维力传感器出货量大幅增长。"],
                "analysis": "核心零部件规模化生产是整机降本的关键支撑。",
                "source": "The Robot Report",
                "image_url": "",
            },
        ],
        "commentary": ["硬件迭代速度正在超越预期。"],
    }


class EmbodiedNewsImageTests(unittest.TestCase):
    def test_extract_image_url_priorities(self):
        # 1. media_content
        entry1 = {"media_content": [{"url": "https://example.com/highres.jpg", "medium": "image"}]}
        self.assertEqual(extract_image_url(entry1), "https://example.com/highres.jpg")

        # 2. media_thumbnail
        entry2 = {"media_thumbnail": [{"url": "https://example.com/thumb.png"}]}
        self.assertEqual(extract_image_url(entry2), "https://example.com/thumb.png")

        # 3. enclosures
        entry3 = {"enclosures": [{"href": "https://example.com/enclosure.webp", "type": "image/webp"}]}
        self.assertEqual(extract_image_url(entry3), "https://example.com/enclosure.webp")

        # 4. summary img tag
        entry4 = {"summary": '<p>Some text</p><img src="https://example.com/inline.jpg" alt="test">'}
        self.assertEqual(extract_image_url(entry4), "https://example.com/inline.jpg")

        # 5. tracker image should be ignored
        entry5 = {"summary": '<img src="https://example.com/pixel.gif" alt="track">'}
        self.assertEqual(extract_image_url(entry5), "")

    def test_render_embodied_article_with_and_without_images(self):
        data = example_embodied()
        # 模拟本地图片已被下载替换为 news_img_1.jpg
        data["news"][0]["image_url"] = "news_img_1.jpg"

        html = render_embodied_article(data, "2026年10月25日")
        soup = BeautifulSoup(html, "html.parser")

        # 检查是否包含封面图 + 1 张新闻配图
        imgs = soup.find_all("img")
        self.assertEqual(len(imgs), 2)
        self.assertIn("news_img_1.jpg", [img.get("src") for img in imgs])
        self.assertIn("▲ 图片来源：IEEE Spectrum", html)

    @patch("fetcher.requests.get")
    def test_download_news_images_success_and_failure(self, mock_get):
        data = example_embodied()

        # 模拟第一张图片下载成功，第二张本来就为空
        mock_resp = Mock(status_code=200, content=b"fake-image-bytes", headers={"Content-Type": "image/jpeg"})
        mock_get.return_value = mock_resp

        with tempfile.TemporaryDirectory() as tmp_dir:
            updated_data = download_news_images(data, tmp_dir)
            self.assertEqual(updated_data["news"][0]["image_url"], "news_img_1.jpg")
            self.assertTrue((Path(tmp_dir) / "news_img_1.jpg").exists())

        # 模拟下载返回 404
        mock_get.return_value = Mock(status_code=404)
        data2 = example_embodied()
        with tempfile.TemporaryDirectory() as tmp_dir:
            updated_data2 = download_news_images(data2, tmp_dir)
            self.assertEqual(updated_data2["news"][0]["image_url"], "")

    def test_clean_old_history_keeps_specified_count(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            folders = [
                "2026-09-01_10-00-00",
                "2026-09-08_10-00-00",
                "2026-09-15_10-00-00",
                "2026-09-22_10-00-00",
                "2026-09-29_10-00-00",
            ]
            for f in folders:
                os.makedirs(os.path.join(tmp_dir, f))

            clean_old_history(tmp_dir, keep_count=3)
            remaining = sorted(os.listdir(tmp_dir))
            self.assertEqual(remaining, [
                "2026-09-15_10-00-00",
                "2026-09-22_10-00-00",
                "2026-09-29_10-00-00",
            ])


if __name__ == "__main__":
    unittest.main()
