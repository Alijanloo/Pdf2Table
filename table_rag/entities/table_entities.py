from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
import numpy as np


class BoundingBox(BaseModel):
    """Value object representing a bounding box."""
    x_min: int
    y_min: int
    x_max: int
    y_max: int

    # Remove custom __init__ - Pydantic handles this automatically

    @validator('x_min', 'y_min', 'x_max', 'y_max')
    def check_non_negative(cls, value):
        if value < 0:
            raise ValueError("Bounding box coordinates must be non-negative")
        return value

    @validator('x_max')
    def x_max_greater_than_x_min(cls, value, values):
        if 'x_min' in values and values['x_min'] >= value:
            raise ValueError("x_max must be greater than x_min")
        return value

    @validator('y_max')
    def y_max_greater_than_y_min(cls, value, values):
        if 'y_min' in values and values['y_min'] >= value:
            raise ValueError("y_max must be greater than y_min")
        return value
    
    @property
    def width(self) -> int:
        return self.x_max - self.x_min
    
    @property
    def height(self) -> int:
        return self.y_max - self.y_min
    
    @property
    def area(self) -> int:
        return self.width * self.height
    
    @property
    def center_x(self) -> float:
        return (self.x_min + self.x_max) / 2
    
    @property
    def center_y(self) -> float:
        return (self.y_min + self.y_max) / 2
    
    def to_list(self) -> List[int]:
        return [self.x_min, self.y_min, self.x_max, self.y_max]
    
    def overlaps_with(self, other: 'BoundingBox') -> bool:
        """Check if this bounding box overlaps with another."""
        return not (self.x_max <= other.x_min or other.x_max <= self.x_min or
                   self.y_max <= other.y_min or other.y_max <= self.y_min)


class DetectedCell(BaseModel):
    """Entity representing a detected table cell."""
    box: BoundingBox
    cell_type: str
    confidence_score: float = Field(..., ge=0, le=1)
    image_crop: Optional[np.ndarray] = None

    # Remove custom __init__ - Pydantic handles this automatically

    class Config:
        arbitrary_types_allowed = True

    @validator('cell_type')
    def cell_type_not_empty(cls, value):
        if not value.strip():
            raise ValueError("Cell type cannot be empty")
        return value
    
    @property
    def is_high_confidence(self) -> bool:
        return self.confidence_score >= 0.6


class GridCell(BaseModel):
    """Entity representing a cell in a table grid."""
    row: int = Field(..., ge=0)
    col: int = Field(..., ge=0)
    text: str
    box: BoundingBox
    cell_type: str = "table cell"
    confidence_score: float = Field(0.0, ge=0, le=1)
    
    # Remove custom __init__ - Pydantic handles this automatically
    
    @property
    def is_empty(self) -> bool:
        return not self.text.strip()
    
    @property
    def is_header(self) -> bool:
        return self.row == 0 or "header" in self.cell_type.lower()


class TableGrid(BaseModel):
    """Entity representing a structured table grid."""
    cells: List[GridCell]
    n_rows: int = Field(..., gt=0)
    n_cols: int = Field(..., gt=0)
    table_box: BoundingBox
    
    # Remove custom __init__ - Pydantic handles this automatically
    
    @validator('cells')
    def check_basic_cell_validity(cls, cells, values):
        """Basic validation - just ensure cells have valid positions."""
        if 'n_rows' in values and 'n_cols' in values:
            n_rows = values['n_rows']
            n_cols = values['n_cols']
            for cell in cells:
                if not (0 <= cell.row < n_rows and 0 <= cell.col < n_cols):
                    raise ValueError(f"Cell position ({cell.row}, {cell.col}) exceeds grid dimensions ({n_rows}x{n_cols})")
        return cells
    
    def get_cell(self, row: int, col: int) -> Optional[GridCell]:
        """Get cell at specific position."""
        for cell in self.cells:
            if cell.row == row and cell.col == col:
                return cell
        return None
    
    def get_headers(self) -> List[str]:
        """Extract header row text."""
        headers = [""] * self.n_cols
        for cell in self.cells:
            if cell.row == 0:
                if 0 <= cell.col < self.n_cols: # Ensure col index is within bounds
                    headers[cell.col] = cell.text.strip()
        return headers
    
    def to_row_format(self) -> List[Dict[str, str]]:
        """Convert grid to list of row dictionaries."""
        headers = self.get_headers()
        rows_data = []
        
        for r_idx in range(1, self.n_rows):
            row_dict = {}
            for c_idx in range(self.n_cols):
                header = headers[c_idx] if c_idx < len(headers) else f"Column{c_idx + 1}"
                cell = self.get_cell(r_idx, c_idx)
                row_dict[header] = cell.text.strip() if cell else ""
            rows_data.append(row_dict)
        
        return rows_data


class DetectedTable(BaseModel):
    """Entity representing a detected table."""
    detection_box: BoundingBox
    confidence_score: float = Field(..., ge=0, le=1)
    page_number: int = Field(..., ge=0)
    source_file: str
    grid: Optional[TableGrid] = None

    @validator('source_file')
    def source_file_not_empty(cls, value):
        if not value.strip():
            raise ValueError("Source file cannot be empty")
        return value
    
    @property
    def is_structured(self) -> bool:
        return self.grid is not None
    
    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "detection_score": self.confidence_score,
            "page_number": self.page_number,
            "source_file": self.source_file,
            "box": self.detection_box.to_list(),
            "n_rows": self.grid.n_rows if self.grid else 0,
            "n_cols": self.grid.n_cols if self.grid else 0,
        }


class PageImage(BaseModel):
    """Entity representing a PDF page image."""
    page_number: int = Field(..., ge=0)
    image_data: np.ndarray
    source_file: str

    class Config:
        arbitrary_types_allowed = True

    @validator('image_data')
    def image_data_not_empty(cls, value):
        if not isinstance(value, np.ndarray) or value.size == 0:
            raise ValueError("Image data must be a non-empty numpy array")
        return value

    @validator('source_file')
    def source_file_not_empty(cls, value):
        if not value.strip():
            raise ValueError("Source file cannot be empty")
        return value
    
    @property
    def width(self) -> int:
        return self.image_data.shape[1]
    
    @property
    def height(self) -> int:
        return self.image_data.shape[0]
    
    @property
    def dimensions(self) -> tuple:
        return (self.height, self.width)
