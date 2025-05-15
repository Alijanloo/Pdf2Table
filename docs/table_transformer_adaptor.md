# TableTransformerAdaptor: Detailed Documentation

This document provides an in-depth explanation of the `TableTransformerAdaptor` class, its core logic, and the important ideas behind its implementation. Each section references the relevant parts of the code to help you understand how the adaptor processes PDF documents to extract structured tables using Microsoft's Table Transformer models.

---

## Overview

The `TableTransformerAdaptor` class is designed to:
- Detect tables in PDF page images.
- Recognize the structure of detected tables (rows and columns).
- Assign cell indices and extract structured data.
- Provide utilities for downstream processing.

It leverages two Microsoft Table Transformer models:
- **Detection model**: Locates tables in a page image.
- **Structure model**: Identifies rows and columns within a table.(Then we Identify the grid cells based on these rows and columns coordinates)

---

## 2. Page Image Extraction

**Relevant code:**  
```python
def extract_page_image(self, pdf_path: str, page_number: int) -> np.ndarray
```

- Uses `fitz` (PyMuPDF) to open a PDF and render a page as a high-resolution RGB image.
- Handles RGBA to RGB conversion if needed.

---

## 3. Table Detection

**Relevant code:**  
```python
def detect_tables(self, image: np.ndarray) -> List[Dict[str, Any]]
```

- Applies the detection model to the page image.
- Uses the feature extractor to preprocess the image.
- Runs inference and post-processes the results to extract bounding boxes for tables.
- Returns a list of detected tables with their scores, labels, and bounding boxes.

---

## 4. Table Structure Recognition

**Relevant code:**  
```python
def recognize_table_structure(self, image: np.ndarray, table_box: List[int]) -> Dict[str, Any]
```

- Crops the detected table region from the page image.
- Applies the structure model to the cropped table image.
- Extracts bounding boxes and types for detected table elements (rows, columns, headers, spanning cells).
- Converts relative cell coordinates to absolute coordinates in the page.
- Calls `_group_into_rows_and_columns` to cluster detected rows and columns.
- Calls `_assign_row_col_indices` to assign each cell to a grid position.

---

## 5. Grouping Rows and Columns

**Relevant code:**  
```python
def _group_into_rows_and_columns(self, cells: List[Dict[str, Any]]) -> Tuple[List[int], List[int]]
```

- Separates detected cells into row and column candidates.
- Filters out spurious wide columns that may contain other columns (to handle model artifacts).
- Computes the center positions of rows and columns.
- Uses `_cluster_coordinates` to merge close centers into single boundaries.
- Handles cases where rows or columns are missing by estimating their positions.
- Returns lists of clustered row and column centers.

---

## 6. Clustering Coordinates

**Relevant code:**  
```python
def _cluster_coordinates(self, coords: List[float], threshold: float = 20.0) -> List[int]
```

- Sorts and deduplicates coordinates.
- Computes differences between consecutive coordinates to estimate a clustering threshold.
- Clusters coordinates that are close together (within the threshold).
- Returns the center of each cluster as the representative boundary.

---

## 7. Assigning Row and Column Indices

**Relevant code:**  
```python
def _assign_row_col_indices(self, cells: List[Dict[str, Any]], rows: List[int], cols: List[int]) -> List[Dict[str, Any]]
```

- Collects all unique x and y edges from cell bounding boxes.
- Clusters these edges to form row and column boundaries.
- For each detected cell, assigns it to all grid positions (row, col) it overlaps.
- For each grid position, keeps the cell with the highest score.
- Fills empty grid positions with estimated bounding boxes.

---

## 8. Table Extraction Pipeline

**Relevant code:**  
```python
def extract_tables(self, pdf_path: str, page_number: int) -> List[Dict[str, Any]]
```

- Extracts the page image.
- Detects tables on the page.
- For each detected table, recognizes its structure and converts it to row format.
- Returns a list of structured tables with metadata.

---

## 9. Row-Format Conversion

**Relevant code:**  
```python
def _convert_to_row_format(self, table_structure: Dict[str, Any]) -> List[Dict[str, str]]
```

- Converts the cell grid into a list of dictionaries, one per row.
- Uses the first row as headers. (should be changed to use the actual header row labels)
- Maps each cell's text to the appropriate header and column.

---

## 11. Handling Model Artifacts

**Relevant code:**  
See `_group_into_rows_and_columns`  
- Filters out wide columns that may be artifacts of the structure model.
- Adjusts clustering thresholds dynamically based on the spread of detected centers.

---

## 12. Robustness Features

- Handles missing or spurious row/column detections by estimating grid positions.
- Clusters noisy detections to avoid over-segmentation.
- Fills empty grid positions for a complete table grid.

---

## Summary Table

| Function                              | Purpose                                                      |
|----------------------------------------|--------------------------------------------------------------|
| `__init__`                            | Model and extractor setup                                    |
| `extract_page_image`                   | PDF page to image                                            |
| `detect_tables`                        | Table detection on page image                                |
| `recognize_table_structure`            | Table structure detection and cell extraction                |
| `_group_into_rows_and_columns`         | Cluster detected rows/columns                                |
| `_cluster_coordinates`                 | Merge close coordinates for grid boundaries                  |
| `_assign_row_col_indices`              | Assign cells to grid, handle overlaps and empty positions    |
| `extract_tables`                       | Full pipeline: detect, structure, and format tables          |
| `_convert_to_row_format`               | Convert grid to row-wise dictionary format                   |

---

## Tips for Debugging and Extension

- Use the visualization utility to inspect grid alignment.
- Adjust clustering thresholds in `_cluster_coordinates` and `_assign_row_col_indices` if your tables are over/under-segmented.
- If you encounter wide columns or merged cells, review the filtering logic in `_group_into_rows_and_columns`.
- For new table layouts, consider extending the logic for header or spanning cell detection.
