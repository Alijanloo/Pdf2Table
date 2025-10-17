from typing import Optional
from pdf2table.usecases.dtos import TableExtractionResponse
from pdf2table.usecases.table_extraction_use_case import TableExtractionUseCase


class TableExtractionAdapter:
    """Adapter that orchestrates table extraction using the use case."""

    def __init__(self, table_extraction_use_case: TableExtractionUseCase):
        self._use_case = table_extraction_use_case

    def extract_tables(
        self, pdf_path: str, page_number: Optional[int] = None
    ) -> TableExtractionResponse:
        """
        Extract tables from a PDF document.

        Args:
            pdf_path: Path to the PDF file
            page_number: Optional page number to extract. If None, extracts from all pages.

        Returns:
            TableExtractionResponse containing extracted tables
        """
        try:
            tables = self._use_case.extract_tables(pdf_path, page_number)

            return TableExtractionResponse(tables=tables, source_file=pdf_path)

        except Exception as e:
            return TableExtractionResponse.error(
                error_message=str(e), source_file=pdf_path
            )
