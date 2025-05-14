import unittest
import os
import numpy as np

from table_rag.adaptors.table_transformer_adaptor import TableTransformerAdaptor
from table_rag import DEFAULT_PATH


class TestTableTransformerAdaptor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.adaptor = TableTransformerAdaptor(device="cpu")

        cls.sample_pdf = os.path.abspath(
            f"{DEFAULT_PATH}/tests/samples/A_Comprehensive_Review_of_Low_Rank_Adaptation_in_Large_Language_Models_for_Efficient_Parameter_Tuning-1.pdf"
        )

        if not os.path.exists(cls.sample_pdf):
            raise FileNotFoundError(f"Sample PDF not found at {cls.sample_pdf}")

    def test_extract_page_image(self):
        image = self.adaptor.extract_page_image(self.sample_pdf, 0)

        self.assertIsInstance(image, np.ndarray)
        self.assertEqual(len(image.shape), 3)
        self.assertTrue(image.shape[2] in [3, 4])

        self.assertGreater(image.shape[0], 0)
        self.assertGreater(image.shape[1], 0)

    def test_detect_tables(self):
        image = self.adaptor.extract_page_image(self.sample_pdf, 0)

        tables = self.adaptor.detect_tables(image)

        self.assertIsInstance(tables, list)

        for table in tables:
            self.assertIn("score", table)
            self.assertIn("label", table)
            self.assertIn("box", table)
            self.assertEqual(len(table["box"]), 4)

    def test_recognize_table_structure(self):
        image = self.adaptor.extract_page_image(self.sample_pdf, 0)

        tables = self.adaptor.detect_tables(image)

        if not tables:
            self.skipTest("No tables detected in the first page")

        table_info = tables[0]

        structure = self.adaptor.recognize_table_structure(image, table_info["box"])

        self.assertIn("cells", structure)
        self.assertIn("n_rows", structure)
        self.assertIn("n_cols", structure)
        self.assertIn("box", structure)

        for cell in structure["cells"]:
            self.assertIn("row", cell)
            self.assertIn("col", cell)
            self.assertIn("text", cell)
            self.assertIn("box", cell)

    def test_real_table_extraction(self):
        tables = self.adaptor.extract_tables(self.sample_pdf, 4)

        self.assertIsInstance(tables, list)

        for table in tables:
            self.assertIn("metadata", table)
            self.assertIn("data", table)
            self.assertIn("box", table)
            self.assertIn("n_rows", table)
            self.assertIn("n_cols", table)
            self.assertIn("raw_structure", table)

            self.assertIn("detection_score", table["metadata"])
            self.assertIn("page_number", table["metadata"])
            self.assertIn("source_file", table["metadata"])

            self.assertIsInstance(table["data"], list)

            if table["data"]:
                row = table["data"][0]
                self.assertIsInstance(row, dict)

                self.assertGreater(len(row.keys()), 0)


if __name__ == "__main__":
    unittest.main(defaultTest="TestTableTransformerAdaptor.test_extract_page_image")
