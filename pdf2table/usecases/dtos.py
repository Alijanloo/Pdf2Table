from typing import List

from pdf2table.entities.table_entities import  DetectedTable


class TableExtractionResponse:    
    def __init__(self, tables: List[DetectedTable], source_file: str):
        self.tables = tables
        self.source_file = source_file
        self.success = True
        self.error_message = None
    
    @classmethod
    def error(cls, error_message: str, source_file: str):
        """Create error response."""
        response = cls([], source_file)
        response.success = False
        response.error_message = error_message
        return response
    
    def to_dict(self):
        """Convert response to dictionary format."""
        if not self.success:
            return {
                "success": False,
                "error": self.error_message,
                "source_file": self.source_file
            }
        
        return {
            "success": True,
            "source_file": self.source_file,
            "tables": [
                {
                    "metadata": table.metadata,
                    "data": table.grid.to_row_format() if table.grid else [],
                }
                for table in self.tables
            ]
        }

