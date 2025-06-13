from table_rag.usecases.table_extraction_use_case import TableExtractionUseCase
from table_rag.usecases.dtos import TableExtractionRequest
from table_rag.adaptors.table_extraction_adaptor import TableExtractionAdapter
from table_rag.frameworks.pdf_image_extractor import PyMuPDFImageExtractor
from table_rag.frameworks.table_transformer_detector import TableTransformerDetector
from table_rag.frameworks.table_structure_recognizer import TableTransformerStructureRecognizer
from table_rag.frameworks.ocr_service import TrOCRService


class TableExtractionFactory:
    """Factory for creating table extraction components following Clean Architecture."""
    
    @staticmethod
    def create_table_extraction_adapter(
        device: str = "cpu",
        detection_threshold: float = 0.9,
        structure_threshold: float = 0.6,
        pdf_dpi: int = 300
    ) -> TableExtractionAdapter:
        """Create a fully configured table extraction adapter."""
        
        # Create framework implementations (outermost layer)
        pdf_extractor = PyMuPDFImageExtractor(dpi=pdf_dpi)
        table_detector = TableTransformerDetector(
            device=device,
            confidence_threshold=detection_threshold
        )
        structure_recognizer = TableTransformerStructureRecognizer(
            device=device,
            confidence_threshold=structure_threshold
        )
        ocr_service = TrOCRService(device=device)
        
        # Create use case (application layer)
        table_extraction_use_case = TableExtractionUseCase(
            pdf_extractor=pdf_extractor,
            table_detector=table_detector,
            structure_recognizer=structure_recognizer,
            ocr_service=ocr_service
        )
        
        # Create adapter (interface layer)
        adapter = TableExtractionAdapter(table_extraction_use_case)
        
        return adapter
    

# Convenience function for backward compatibility
def create_table_transformer_adaptor(device: str = "cpu") -> TableExtractionAdapter:
    """Create table transformer adapter - maintains interface compatibility."""
    return TableExtractionFactory.create_table_extraction_adapter(device)


class TableExtractionService:
    """High-level service interface for table extraction."""
    
    def __init__(self, device: str = "cpu"):
        self._adapter = TableExtractionFactory.create_table_extraction_adapter(device)

    def extract_tables_from_page(self, pdf_path: str, page_number: int) -> dict:
        """Extract tables from a single PDF page."""
        request = TableExtractionRequest(pdf_path, page_number)
        response = self._adapter.extract_tables(request)
        return response.to_dict()
    
    def extract_tables_from_pdf(self, pdf_path: str) -> list[dict]:
        """Extract tables from all pages of a PDF."""
        from table_rag.frameworks.pdf_image_extractor import PyMuPDFImageExtractor
        
        # Get page count
        pdf_extractor = PyMuPDFImageExtractor()
        page_count = pdf_extractor.get_page_count(pdf_path)
        
        results = []
        for page_number in range(page_count):
            try:
                result = self.extract_tables_from_page(pdf_path, page_number)
                results.append(result)
            except Exception as e:
                # Add error result for this page
                results.append({
                    "success": False,
                    "error": str(e),
                    "page_number": page_number,
                    "source_file": pdf_path
                })
        
        return results
