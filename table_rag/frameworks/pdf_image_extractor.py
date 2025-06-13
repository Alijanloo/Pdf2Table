import cv2
import numpy as np
import fitz
from typing import Optional

from table_rag.entities.table_entities import PageImage
from table_rag.adaptors.table_extraction_adaptor import PDFImageExtractorInterface


class PyMuPDFImageExtractor(PDFImageExtractorInterface):
    """Concrete implementation of PDF image extraction using PyMuPDF."""
    
    def __init__(self, dpi: int = 300):
        self.dpi = dpi
    
    def extract_page_image(self, pdf_path: str, page_number: int) -> PageImage:
        """Extract image from PDF page using PyMuPDF."""
        try:
            doc = fitz.open(pdf_path)
            
            if page_number >= doc.page_count or page_number < 0:
                raise ValueError(f"Page number {page_number} is out of range for document with {doc.page_count} pages")
            
            page = doc[page_number]
            pix = page.get_pixmap(dpi=self.dpi)
            
            # Convert to numpy array
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
            
            # Convert RGBA to RGB if necessary
            if img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
            
            doc.close()
            
            return PageImage(
                page_number=page_number,
                image_data=img,
                source_file=pdf_path
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to extract image from page {page_number}: {str(e)}")
    
    def get_page_count(self, pdf_path: str) -> int:
        """Get total number of pages in PDF."""
        try:
            doc = fitz.open(pdf_path)
            count = doc.page_count
            doc.close()
            return count
        except Exception as e:
            raise RuntimeError(f"Failed to get page count: {str(e)}")
