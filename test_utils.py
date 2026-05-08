import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import utils


class TestUtils(unittest.TestCase):
    def test_build_save_kwargs_jpeg(self):
        result = utils._build_save_kwargs(".jpg", 90)
        self.assertEqual(result["format"], "JPEG")
        self.assertEqual(result["quality"], 90)
        self.assertTrue(result["optimize"])

    def test_build_save_kwargs_png(self):
        result = utils._build_save_kwargs(".png", 90)
        self.assertEqual(result["format"], "PNG")
        self.assertTrue(result["optimize"])
        self.assertNotIn("quality", result)

    def test_build_save_kwargs_webp(self):
        result = utils._build_save_kwargs(".webp", 80)
        self.assertEqual(result["format"], "WEBP")
        self.assertEqual(result["quality"], 80)

    def test_build_save_kwargs_unknown(self):
        result = utils._build_save_kwargs(".tiff", 80)
        self.assertEqual(result, {})

    def test_crop_from_annotations_invalid_file(self):
        result = utils.crop_from_annotations("nofile.png", "noann.csv", "outdir")
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
