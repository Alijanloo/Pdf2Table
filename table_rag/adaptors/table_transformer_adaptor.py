from typing import List, Dict, Any, Tuple

import cv2
import numpy as np
import torch
import fitz
import os
from transformers import DetrFeatureExtractor, TableTransformerForObjectDetection

from table_rag.utils.table_visualization import visualize_cell_grid

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
        self.structure_feature_extractor.size["shortest_edge"] = 800

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

        result = {
            "cells": cell_grid,
            "n_rows": len(rows),
            "n_cols": len(cols),
            "box": table_box,
        }

        # uncomment this to visualize the cell grid
        # visualize_cell_grid(cell_grid, table_image)

        return result

    def _group_into_rows_and_columns(
        self, cells: List[Dict[str, Any]]
    ) -> Tuple[List[int], List[int]]:

        row_cells = [cell for cell in cells if "table row" in cell["type"]]
        col_cells = [cell for cell in cells if "table column" in cell["type"]]

        filtered_col_cells = col_cells.copy()
        if len(col_cells) > 1:

            sorted_by_width = sorted(col_cells, key=lambda c: c["relative_box"][2] - c["relative_box"][0])

            widest_column = sorted_by_width[-1]
            widest_width = widest_column["relative_box"][2] - widest_column["relative_box"][0]

            avg_width = sum([(c["relative_box"][2] - c["relative_box"][0]) 
                           for c in sorted_by_width[:-1]]) / max(1, len(sorted_by_width) - 1)

            contains_other_columns = False
            for col in col_cells:
                if col != widest_column:

                    if (col["relative_box"][0] >= widest_column["relative_box"][0] and 
                        col["relative_box"][2] <= widest_column["relative_box"][2]):
                        contains_other_columns = True
                        break

            if contains_other_columns or widest_width > 3 * avg_width:
                filtered_col_cells = [c for c in col_cells if c != widest_column]
                print(f"Filtered out a wide column ({widest_width:.1f}px) that contains other columns")

        has_rows = len(row_cells) > 0
        has_cols = len(filtered_col_cells) > 0

        y_min_vals = [cell["relative_box"][1] for cell in cells]
        y_max_vals = [cell["relative_box"][3] for cell in cells]
        x_min_vals = [cell["relative_box"][0] for cell in cells]
        x_max_vals = [cell["relative_box"][2] for cell in cells]
        
        if not y_min_vals or not y_max_vals or not x_min_vals or not x_max_vals:
            return [], []

        table_y_min = min(y_min_vals)
        table_y_max = max(y_max_vals)
        table_x_min = min(x_min_vals)
        table_x_max = max(x_max_vals)

        row_centers = []
        col_centers = []

        if has_rows:
            for cell in row_cells:
                y_min, y_max = cell["relative_box"][1], cell["relative_box"][3]
                row_centers.append((y_min + y_max) / 2)
        else:

            for cell in cells:
                y_min, y_max = cell["relative_box"][1], cell["relative_box"][3]
                row_centers.append((y_min + y_max) / 2)

        rows = self._cluster_coordinates(row_centers)

        if has_cols:

            sorted_col_cells = sorted(filtered_col_cells, key=lambda c: c["relative_box"][0])

            cols = [(c["relative_box"][0] + c["relative_box"][2]) / 2 for c in sorted_col_cells]
        else:

            for cell in cells:
                x_min, x_max = cell["relative_box"][0], cell["relative_box"][2]
                col_centers.append((x_min + x_max) / 2)
            cols = self._cluster_coordinates(col_centers)

        min_rows = 1
        min_cols = 1

        if len(rows) < min_rows or len(cols) < min_cols:

            if has_rows:
                estimated_row_count = len(row_cells)
            else:
                estimated_row_count = max(
                    min_rows, len(set([cell["relative_box"][1] for cell in cells]))
                )

            if len(rows) < min_rows:
                rows = [
                    table_y_min + i * (table_y_max - table_y_min) / estimated_row_count
                    for i in range(estimated_row_count)
                ]

            if len(cols) < min_cols:

                if has_cols:
                    estimated_col_count = len(filtered_col_cells)
                else:
                    estimated_col_count = max(
                        min_cols, len(set([cell["relative_box"][0] for cell in cells]))
                    )
                
                cols = [
                    table_x_min + i * (table_x_max - table_x_min) / estimated_col_count
                    for i in range(estimated_col_count)
                ]

        return rows, cols

    def _cluster_coordinates(
        self, coords: List[float], threshold: float = 20.0
    ) -> List[int]:
        if not coords:
            return []

        coords = sorted(set(coords))

        if len(coords) > 2:
            differences = [coords[i+1] - coords[i] for i in range(len(coords)-1)]
            if differences:

                median_diff = sorted(differences)[len(differences)//2]

                # Adjusting threshold for too high or low median_diffs
                threshold = max(threshold, median_diff * 0.7)
                if median_diff < 5:
                    threshold = min(threshold, median_diff * 2)

        clusters = [[coords[0]]]

        for coord in coords[1:]:
            if coord - clusters[-1][-1] < threshold:
                clusters[-1].append(coord)
            else:
                clusters.append([coord])

        cluster_centers = [sum(cluster) / len(cluster) for cluster in clusters]

        if len(cluster_centers) > 1:
            final_centers = [cluster_centers[0]]
            for center in cluster_centers[1:]:

                if center - final_centers[-1] < threshold/2:
                    continue
                final_centers.append(center)
            return final_centers
            
        return cluster_centers

    def _assign_row_col_indices(
        self, cells: List[Dict[str, Any]], rows: List[int], cols: List[int]
    ) -> List[Dict[str, Any]]:
        if not rows or not cols:
            return []

        def cluster_edges(edges, threshold=10):
            if not edges:
                return []
            edges = sorted(edges)
            clusters = [[edges[0]]]
            for e in edges[1:]:
                if abs(e - clusters[-1][-1]) < threshold:
                    clusters[-1].append(e)
                else:
                    clusters.append([e])
            return [int(sum(cluster) / len(cluster)) for cluster in clusters]

        y_edges = set()
        x_edges = set()
        for cell in cells:
            if "relative_box" in cell and len(cell["relative_box"]) == 4:
                x_edges.add(cell["relative_box"][0])
                x_edges.add(cell["relative_box"][2])
                y_edges.add(cell["relative_box"][1])
                y_edges.add(cell["relative_box"][3])
        row_boundaries = cluster_edges(list(y_edges), threshold=10)
        col_boundaries = cluster_edges(list(x_edges), threshold=10)
        n_rows = len(row_boundaries) - 1
        n_cols = len(col_boundaries) - 1
        if n_rows <= 0 or n_cols <= 0:
            return []

        grid = {}
        for cell in cells:
            if "relative_box" not in cell or len(cell["relative_box"]) != 4:
                continue
            c_xmin, c_ymin, c_xmax, c_ymax = cell["relative_box"][0], cell["relative_box"][1], cell["relative_box"][2], cell["relative_box"][3]
            for r in range(n_rows):

                if not (c_ymax > row_boundaries[r] and c_ymin < row_boundaries[r+1]):
                    continue
                for c in range(n_cols):

                    if not (c_xmax > col_boundaries[c] and c_xmin < col_boundaries[c+1]):
                        continue
                    pos = (r, c)
                    if pos not in grid or cell.get("score", 0) > grid[pos].get("score", 0):
                        grid[pos] = cell

        cell_grid = []
        for r in range(n_rows):
            for c in range(n_cols):
                pos = (r, c)
                if pos in grid:
                    cell = grid[pos]
                    cell_text = cell.get("text", "") if "cell_img" in cell else ""
                    cell_with_indices = {
                        "row": r,
                        "col": c,
                        "text": cell_text,
                        "box": [col_boundaries[c], row_boundaries[r], col_boundaries[c+1], row_boundaries[r+1]],
                        "type": "table cell",
                        "score": cell.get("score", 0)
                    }
                else:

                    est_box = [
                        int(col_boundaries[c]),
                        int(row_boundaries[r]),
                        int(col_boundaries[c+1]),
                        int(row_boundaries[r+1])
                    ]
                    cell_with_indices = {
                        "row": r,
                        "col": c,
                        "text": "",
                        "box": est_box,
                        "type": "table cell",
                        "score": 0
                    }
                cell_grid.append(cell_with_indices)
        cell_grid.sort(key=lambda cell: (cell["row"], cell["col"]))
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
