import cv2
import numpy as np
import fitz

from pdf2table.entities.table_entities import PageImage
from pdf2table.usecases.interfaces.framework_interfaces import (
    PDFImageExtractorInterface,
)


class PyMuPDFImageExtractor(PDFImageExtractorInterface):
    """Concrete implementation of PDF image extraction using PyMuPDF."""

    def __init__(self, dpi: int = 300):
        self.dpi = dpi

    def extract_page_image(self, pdf_path: str, page_number: int) -> PageImage:
        """Extract image from PDF page using PyMuPDF."""
        try:
            doc = fitz.open(pdf_path)

            if page_number >= doc.page_count or page_number < 0:
                raise ValueError(
                    f"Page number {page_number} is out of range for document with {doc.page_count} pages"
                )

            page = doc[page_number]
            pix = page.get_pixmap(dpi=self.dpi)

            # Convert to numpy array
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                pix.h, pix.w, pix.n
            )

            # Convert RGBA to RGB if necessary
            if img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)

            words = self.calculate_words_coordinates(page, img)

            doc.close()

            return PageImage(
                page_number=page_number,
                image_data=img,
                source_file=pdf_path,
                words=words,
            )

        except Exception as e:
            raise RuntimeError(
                f"Failed to extract image from page {page_number}: {str(e)}"
            )

    def calculate_words_coordinates(self, page: fitz.Page, img: np.ndarray) -> list:
        """
        Calculates the coordinates of words on a PDF page mapped to the corresponding image pixel coordinates.

        Args:
            page (fitz.Page): The PDF page object from PyMuPDF.
            img (np.ndarray): The image array representing the rendered PDF page.

        Returns:
            list: A list of tuples, each containing the bounding box coordinates (x0, y0, x1, y1) in image pixels
                  and the word string (x0, y0, x1, y1, word).
        """
        words = page.get_text("words")
        pdf_width, pdf_height = page.rect.width, page.rect.height
        img_width, img_height = img.shape[1], img.shape[0]

        def pdf_to_img_x(x):
            return x * (img_width / pdf_width)

        def pdf_to_img_y(y):
            return y * (img_height / pdf_height)

        words_img = []
        for w in words:
            x0 = int(round(pdf_to_img_x(w[0])))
            x1 = int(round(pdf_to_img_x(w[2])))
            y1 = int(round(pdf_to_img_y(w[3])))  # due to reversion issue
            y0 = int(round(pdf_to_img_y(w[1])))
            words_img.append((x0, y0, x1, y1, w[4]))
        return words_img

    def get_page_count(self, pdf_path: str) -> int:
        """Get total number of pages in PDF."""
        try:
            doc = fitz.open(pdf_path)
            count = doc.page_count
            doc.close()
            return count
        except Exception as e:
            raise RuntimeError(f"Failed to get page count: {str(e)}")
