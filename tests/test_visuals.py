import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import visuals


class SceneImageTests(unittest.TestCase):
    def test_uses_deepai_generated_scene_art(self):
        generator = mock.Mock()
        generator.generate.return_value = Image.new("RGB", (640, 640), "purple")
        with tempfile.TemporaryDirectory() as folder, \
                mock.patch.object(visuals, "DeepAIImageGenerator", return_value=generator), \
                mock.patch.object(visuals, "fetch_pexels") as pexels:
            paths = visuals.create_scene_images(
                [{"visual_query": "a mountain", "caption": "Mountains"}],
                "A title",
                Path(folder),
            )
            self.assertTrue(paths[0].is_file())

        generator.generate.assert_called_once()
        generator.close.assert_called_once()
        pexels.assert_not_called()

    def test_falls_back_after_deepai_becomes_unavailable(self):
        generator = mock.Mock()
        generator.generate.side_effect = visuals.DeepAIUnavailableError("rate limit")
        with tempfile.TemporaryDirectory() as folder, \
                mock.patch.object(visuals, "DeepAIImageGenerator", return_value=generator), \
                mock.patch.object(
                    visuals,
                    "fetch_pexels",
                    return_value=Image.new("RGB", (640, 640), "blue"),
                ) as pexels:
            paths = visuals.create_scene_images(
                [
                    {"visual_query": "a mountain", "caption": "Mountains"},
                    {"visual_query": "a river", "caption": "Rivers"},
                ],
                "A title",
                Path(folder),
            )

        self.assertEqual(len(paths), 2)
        self.assertEqual(generator.generate.call_count, 1)
        generator.close.assert_called_once()
        self.assertEqual(pexels.call_count, 2)


if __name__ == "__main__":
    unittest.main()
