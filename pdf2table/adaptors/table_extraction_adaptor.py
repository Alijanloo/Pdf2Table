from pdf2table.usecases.dtos import TableExtractionRequest, TableExtractionResponse
from pdf2table.usecases.table_extraction_use_case import TableExtractionUseCase


class TableExtractionAdapter:
    """Adapter that orchestrates table extraction using the use case."""
    
    def __init__(self, table_extraction_use_case: TableExtractionUseCase):
        self._use_case = table_extraction_use_case
    
    def extract_tables(self, request: TableExtractionRequest) -> TableExtractionResponse:
        try:
            tables = self._use_case.extract_tables_from_page(
                request.pdf_path, 
                request.page_number
            )
            
            return TableExtractionResponse(
                tables=tables,
                page_number=request.page_number,
                source_file=request.pdf_path
            )
            
        except Exception as e:
            return TableExtractionResponse.error(
                error_message=str(e),
                page_number=request.page_number,
                source_file=request.pdf_path
            )
