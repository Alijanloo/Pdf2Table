from abc import ABC, abstractmethod
from typing import List
import numpy as np

from pdf2table.entities.table_entities import (
    PageImage, DetectedTable, DetectedCell, BoundingBox
)


class PDFImageExtractorInterface(ABC):
    """Abstract interface for PDF image extraction."""
    
    @abstractmethod
    def extract_page_image(self, pdf_path: str, page_number: int) -> PageImage:
        """Extract image from PDF page."""
        pass

    @abstractmethod
    def get_page_count(self, pdf_path: str) -> int:
        """Get total number of pages in PDF."""
        pass

class TableDetectorInterface(ABC):
    """Abstract interface for table detection."""
    
    @abstractmethod
    def detect_tables(self, page_image: PageImage) -> List[DetectedTable]:
        """Detect tables in a page image."""
        pass


class TableStructureRecognizerInterface(ABC):
    """Abstract interface for table structure recognition."""
    
    @abstractmethod
    def recognize_structure(self, page_image: PageImage, table_box: BoundingBox) -> List[DetectedCell]:
        """Recognize structure of a detected table."""
        pass


class OCRInterface(ABC):
    """Abstract interface for optical character recognition."""
    
    @abstractmethod
    def extract_text(self, image_crop: np.ndarray) -> str:
        """Extract text from image crop."""
        pass