from typing import List

from table_rag.entities.table_entities import  DetectedTable


class TableExtractionRequest:    
    def __init__(self, pdf_path: str, page_number: int):
        self.pdf_path = pdf_path
        self.page_number = page_number


class TableExtractionResponse:    
    def __init__(self, tables: List[DetectedTable], page_number: int, source_file: str):
        self.tables = tables
        self.page_number = page_number
        self.source_file = source_file
        self.success = True
        self.error_message = None
    
    @classmethod
    def error(cls, error_message: str, page_number: int, source_file: str):
        """Create error response."""
        response = cls([], page_number, source_file)
        response.success = False
        response.error_message = error_message
        return response
    
    def to_dict(self):
        """Convert response to dictionary format."""
        if not self.success:
            return {
                "success": False,
                "error": self.error_message,
                "page_number": self.page_number,
                "source_file": self.source_file
            }
        
        return {
            "success": True,
            "page_number": self.page_number,
            "source_file": self.source_file,
            "tables": [
                {
                    "metadata": table.metadata,
                    "data": table.grid.to_row_format() if table.grid else [],
                    "box": table.detection_box.to_list(),
                    "n_rows": table.grid.n_rows if table.grid else 0,
                    "n_cols": table.grid.n_cols if table.grid else 0,
                }
                for table in self.tables
            ]
        }

