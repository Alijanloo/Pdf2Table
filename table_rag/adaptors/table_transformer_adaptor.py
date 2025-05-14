from typing import List, Dict, Any, Tuple
import cv2
import numpy as np
import torch
import fitz
import os
from transformers import DetrFeatureExtractor, TableTransformerForObjectDetection
from table_rag.entities.models import TableCell


class TableTransformerAdaptor:
    def __init__(
        self,
        detection_model: str = "microsoft/table-transformer-detection",
        structure_model: str = "microsoft/table-transformer-structure-recognition-v1.1-all",
        device: str = "cpu",
    ):
        self.detection_model = TableTransformerForObjectDetection.from_pretrained(
            detection_model
        )
        self.detection_feature_extractor = DetrFeatureExtractor.from_pretrained(
            detection_model
        )

        self.structure_model = TableTransformerForObjectDetection.from_pretrained(
            structure_model
        )
        self.structure_feature_extractor = DetrFeatureExtractor.from_pretrained(
            structure_model
        )

        self.device = device
        self.detection_model.to(self.device)
        self.structure_model.to(self.device)

        self.detection_threshold = 0.9
        self.structure_threshold = 0.6

    def extract_page_image(self, pdf_path: str, page_number: int) -> np.ndarray:
        doc = fitz.open(pdf_path)
        page = doc[page_number]

        pix = page.get_pixmap(dpi=300)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)

        if img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)

        return img

    def detect_tables(self, image: np.ndarray) -> List[Dict[str, Any]]:
        encoding = self.detection_feature_extractor(images=image, return_tensors="pt")

        for k, v in encoding.items():
            encoding[k] = v.to(self.device)

        with torch.no_grad():
            outputs = self.detection_model(**encoding)

        results = self.detection_feature_extractor.post_process_object_detection(
            outputs,
            threshold=self.detection_threshold,
            target_sizes=[(image.shape[0], image.shape[1])],
        )[0]

        tables = []
        for score, label, box in zip(
            results["scores"], results["labels"], results["boxes"]
        ):
            box = [round(i) for i in box.tolist()]
            tables.append(
                {
                    "score": score.item(),
                    "label": self.detection_model.config.id2label[label.item()],
                    "box": box,
                }
            )

        return tables

    def recognize_table_structure(
        self, image: np.ndarray, table_box: List[int]
    ) -> Dict[str, Any]:
        x_min, y_min, x_max, y_max = table_box
        table_image = image[y_min:y_max, x_min:x_max]

        encoding = self.structure_feature_extractor(
            images=table_image,
            size={"height": table_image.shape[0], "width": table_image.shape[1]},
            return_tensors="pt"
        )

        for k, v in encoding.items():
            encoding[k] = v.to(self.device)

        with torch.no_grad():
            outputs = self.structure_model(**encoding)

        results = self.structure_feature_extractor.post_process_object_detection(
            outputs,
            threshold=self.structure_threshold,
            target_sizes=[(table_image.shape[0], table_image.shape[1])],
        )[0]

        cells = []
        for score, label, box in zip(
            results["scores"], results["labels"], results["boxes"]
        ):
            box = [round(i) for i in box.tolist()]

            label_name = self.structure_model.config.id2label[label.item()]

            if label_name in [
                "table column",
                "table row",
                "table column header",
                "table projected row header",
                "table spanning cell",
            ]:
                abs_box = [
                    box[0] + x_min,
                    box[1] + y_min,
                    box[2] + x_min,
                    box[3] + y_min,
                ]

                cell_img = table_image[box[1] : box[3], box[0] : box[2]]

                cells.append(
                    {
                        "score": score.item(),
                        "box": abs_box,
                        "relative_box": box,
                        "type": label_name,
                        "cell_img": cell_img,
                    }
                )

        rows, cols = self._group_into_rows_and_columns(cells)
        cell_grid = self._assign_row_col_indices(cells, rows, cols)

        return {
            "cells": cell_grid,
            "n_rows": len(rows),
            "n_cols": len(cols),
            "box": table_box,
        }

    def _group_into_rows_and_columns(
        self, cells: List[Dict[str, Any]]
    ) -> Tuple[List[int], List[int]]:
        y_min_vals = [cell["relative_box"][1] for cell in cells]
        y_max_vals = [cell["relative_box"][3] for cell in cells]

        x_min_vals = [cell["relative_box"][0] for cell in cells]
        x_max_vals = [cell["relative_box"][2] for cell in cells]

        if y_min_vals and y_max_vals and x_min_vals and x_max_vals:
            table_y_min = min(y_min_vals)
            table_y_max = max(y_max_vals)
            table_x_min = min(x_min_vals)
            table_x_max = max(x_max_vals)

            row_centers = []
            for cell in cells:
                y_min, y_max = cell["relative_box"][1], cell["relative_box"][3]
                row_centers.append((y_min + y_max) / 2)

            col_centers = []
            for cell in cells:
                x_min, x_max = cell["relative_box"][0], cell["relative_box"][2]
                col_centers.append((x_min + x_max) / 2)

            rows = self._cluster_coordinates(row_centers)
            cols = self._cluster_coordinates(col_centers)

            min_rows = 1
            min_cols = 1

            if len(rows) < min_rows or len(cols) < min_cols:
                estimated_row_count = max(
                    min_rows, len(set([cell["relative_box"][1] for cell in cells]))
                )
                estimated_col_count = max(
                    min_cols, len(set([cell["relative_box"][0] for cell in cells]))
                )

                if len(rows) < min_rows:
                    rows = [
                        table_y_min
                        + i * (table_y_max - table_y_min) / estimated_row_count
                        for i in range(estimated_row_count)
                    ]

                if len(cols) < min_cols:
                    cols = [
                        table_x_min
                        + i * (table_x_max - table_x_min) / estimated_col_count
                        for i in range(estimated_col_count)
                    ]

            return rows, cols

        row_centers = []
        col_centers = []

        for cell in cells:
            if "relative_box" in cell:
                y_min, y_max = cell["relative_box"][1], cell["relative_box"][3]
                row_centers.append((y_min + y_max) / 2)

                x_min, x_max = cell["relative_box"][0], cell["relative_box"][2]
                col_centers.append((x_min + x_max) / 2)

        rows = self._cluster_coordinates(row_centers)
        cols = self._cluster_coordinates(col_centers)

        return rows, cols

    def _cluster_coordinates(
        self, coords: List[float], threshold: float = 10.0
    ) -> List[int]:
        if not coords:
            return []

        sorted_coords = sorted(coords)

        clusters = [[sorted_coords[0]]]

        for coord in sorted_coords[1:]:
            if coord - clusters[-1][-1] < threshold:
                clusters[-1].append(coord)
            else:
                clusters.append([coord])

        cluster_centers = [sum(cluster) / len(cluster) for cluster in clusters]

        return cluster_centers

    def _assign_row_col_indices(
        self, cells: List[Dict[str, Any]], rows: List[int], cols: List[int]
    ) -> List[Dict[str, Any]]:
        cell_grid = []

        try:
            import pytesseract

            has_pytesseract = True
        except ImportError:
            has_pytesseract = False
            print(
                "Warning: pytesseract not installed. Cell text extraction will be limited."
            )

        for cell in cells:
            y_center = (cell["relative_box"][1] + cell["relative_box"][3]) / 2
            x_center = (cell["relative_box"][0] + cell["relative_box"][2]) / 2

            row_idx = min(range(len(rows)), key=lambda i: abs(rows[i] - y_center))
            col_idx = min(range(len(cols)), key=lambda i: abs(cols[i] - x_center))

            cell_text = ""
            if "cell_img" in cell and has_pytesseract:
                try:
                    cell_img = cell["cell_img"]
                    if cell_img.size > 0:
                        if len(cell_img.shape) == 3:
                            gray = cv2.cvtColor(cell_img, cv2.COLOR_RGB2GRAY)
                        else:
                            gray = cell_img

                        gray = cv2.equalizeHist(gray)

                        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

                        cell_text = pytesseract.image_to_string(
                            thresh, config="--psm 6"
                        ).strip()

                        if not cell_text:
                            cell_text = pytesseract.image_to_string(
                                gray, config="--psm 6"
                            ).strip()
                except Exception as e:
                    print(f"OCR error: {e}")

            cell_with_indices = {
                "row": row_idx,
                "col": col_idx,
                "text": cell_text,
                "box": cell["box"],
            }

            cell_grid.append(cell_with_indices)

        return cell_grid

    def extract_tables(self, pdf_path: str, page_number: int) -> List[Dict[str, Any]]:
        page_image = self.extract_page_image(pdf_path, page_number)

        detected_tables = self.detect_tables(page_image)

        tables = []

        for table_info in detected_tables:
            table_structure = self.recognize_table_structure(
                page_image, table_info["box"]
            )

            table_structure["metadata"] = {
                "detection_score": table_info["score"],
                "page_number": page_number,
                "source_file": os.path.basename(pdf_path),
            }

            structured_table = self._convert_to_row_format(table_structure)
            tables.append(
                {
                    "metadata": table_structure["metadata"],
                    "data": structured_table,
                    "box": table_structure["box"],
                    "n_rows": table_structure["n_rows"],
                    "n_cols": table_structure["n_cols"],
                    "raw_structure": table_structure,
                }
            )

        return tables

    def _convert_to_row_format(
        self, table_structure: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        cells = table_structure["cells"]

        n_rows = table_structure["n_rows"]
        n_cols = table_structure["n_cols"]

        header_cells = [cell for cell in cells if cell["row"] == 0]
        headers = [""] * n_cols

        for cell in header_cells:
            col_idx = cell["col"]
            if col_idx < n_cols:
                headers[col_idx] = cell["text"].strip()

        rows = []

        for row_idx in range(1, n_rows):
            row_cells = [cell for cell in cells if cell["row"] == row_idx]
            row_data = {}

            for col_idx in range(n_cols):
                header = (
                    headers[col_idx]
                    if col_idx < len(headers)
                    else f"Column{col_idx + 1}"
                )

                cell_value = ""
                for cell in row_cells:
                    if cell["col"] == col_idx:
                        cell_value = cell["text"].strip()
                        break

                row_data[header] = cell_value

            rows.append(row_data)

        return rows

    def visualize_table_detection(
        self, pdf_path: str, page_number: int, save_path: str = None
    ):
        import matplotlib.pyplot as plt
        from PIL import Image

        COLORS = [
            [0.000, 0.447, 0.741],
            [0.850, 0.325, 0.098],
            [0.929, 0.694, 0.125],
            [0.494, 0.184, 0.556],
            [0.466, 0.674, 0.188],
            [0.301, 0.745, 0.933],
        ]

        page_image = self.extract_page_image(pdf_path, page_number)

        pil_img = Image.fromarray(page_image)

        encoding = self.detection_feature_extractor(
            images=page_image, return_tensors="pt"
        )

        for k, v in encoding.items():
            encoding[k] = v.to(self.device)

        with torch.no_grad():
            outputs = self.detection_model(**encoding)

        target_sizes = [(page_image.shape[0], page_image.shape[1])]
        results = self.detection_feature_extractor.post_process_object_detection(
            outputs, threshold=self.detection_threshold, target_sizes=target_sizes
        )[0]

        plt.figure(figsize=(16, 10))
        plt.imshow(pil_img)
        ax = plt.gca()
        colors = COLORS * 100

        for score, label, (xmin, ymin, xmax, ymax), c in zip(
            results["scores"].tolist(),
            results["labels"].tolist(),
            results["boxes"].tolist(),
            colors,
        ):
            ax.add_patch(
                plt.Rectangle(
                    (xmin, ymin),
                    xmax - xmin,
                    ymax - ymin,
                    fill=False,
                    color=c,
                    linewidth=3,
                )
            )
            text = f"{self.detection_model.config.id2label[label]}: {score:0.2f}"
            ax.text(
                xmin, ymin, text, fontsize=15, bbox=dict(facecolor="yellow", alpha=0.5)
            )

        plt.axis("off")
        title = (
            f"Table Detection - {os.path.basename(pdf_path)} - Page {page_number + 1}"
        )
        plt.title(title)

        if save_path:
            plt.savefig(save_path, bbox_inches="tight")
            plt.close()
        else:
            plt.show()

        return results

    def visualize_table_structure(
        self, pdf_path: str, page_number: int, table_idx: int = 0, save_path: str = None
    ):
        import matplotlib.pyplot as plt
        from PIL import Image

        COLORS = [
            [0.000, 0.447, 0.741],
            [0.850, 0.325, 0.098],
            [0.929, 0.694, 0.125],
            [0.494, 0.184, 0.556],
            [0.466, 0.674, 0.188],
            [0.301, 0.745, 0.933],
        ]

        page_image = self.extract_page_image(pdf_path, page_number)

        detected_tables = self.detect_tables(page_image)

        if not detected_tables:
            print(f"No tables detected on page {page_number}")
            return None

        if table_idx >= len(detected_tables):
            print(
                f"Table index {table_idx} out of range, only {len(detected_tables)} tables detected"
            )
            return None

        table_info = detected_tables[table_idx]
        table_box = table_info["box"]

        x_min, y_min, x_max, y_max = table_box
        table_image = page_image[y_min:y_max, x_min:x_max]
        table_pil = Image.fromarray(table_image)

        encoding = self.structure_feature_extractor(
            images=table_image, 
            size={"height": table_image.shape[0], "width": table_image.shape[1]},
            return_tensors="pt"
        )

        for k, v in encoding.items():
            encoding[k] = v.to(self.device)

        with torch.no_grad():
            outputs = self.structure_model(**encoding)

        target_sizes = [(table_image.shape[0], table_image.shape[1])]
        results = self.structure_feature_extractor.post_process_object_detection(
            outputs, threshold=self.structure_threshold, target_sizes=target_sizes
        )[0]

        plt.figure(figsize=(16, 10))
        plt.imshow(table_pil)
        ax = plt.gca()
        colors = COLORS * 100

        for score, label, (xmin, ymin, xmax, ymax), c in zip(
            results["scores"].tolist(),
            results["labels"].tolist(),
            results["boxes"].tolist(),
            colors,
        ):
            ax.add_patch(
                plt.Rectangle(
                    (xmin, ymin),
                    xmax - xmin,
                    ymax - ymin,
                    fill=False,
                    color=c,
                    linewidth=3,
                )
            )
            text = f"{self.structure_model.config.id2label[label]}: {score:0.2f}"
            ax.text(
                xmin, ymin, text, fontsize=12, bbox=dict(facecolor="yellow", alpha=0.5)
            )

        plt.axis("off")
        title = f"Table Structure - {os.path.basename(pdf_path)} - Page {page_number + 1} - Table {table_idx + 1}"
        plt.title(title)

        if save_path:
            plt.savefig(save_path, bbox_inches="tight")
            plt.close()
        else:
            plt.show()

        return results
