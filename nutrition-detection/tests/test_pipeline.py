import tempfile
import unittest
from pathlib import Path

from train import validate_data_yaml


class NutritionDetectionTests(unittest.TestCase):
    def test_accepts_existing_yaml_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.yaml"
            path.write_text("path: dataset\ntrain: images/train\n", encoding="utf-8")
            self.assertEqual(validate_data_yaml(path), path.resolve())

    def test_rejects_missing_dataset_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.yaml"
            with self.assertRaises(FileNotFoundError):
                validate_data_yaml(path)

    def test_rejects_non_yaml_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.json"
            path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "yaml"):
                validate_data_yaml(path)


if __name__ == "__main__":
    unittest.main()
