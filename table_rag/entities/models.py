from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class TableCell:
    row: int
    col: int
    text: str
    box: List[int]


@dataclass
class Table:
    cells: List[TableCell]
    n_rows: int
    n_cols: int
    box: List[int]
    metadata: Dict[str, Any]


@dataclass
class PDFPage:
    page_number: int
    content: str
    tables: List[Table]


@dataclass
class PDFDocument:
    filename: str
    pages: List[PDFPage]
    tables: List[Table]
