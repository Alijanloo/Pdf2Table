# Table Extraction Module

## Directory Structure
```
table_rag/
├── entities/
│   └── table_entities.py
├── usecases/
│   ├── dtos.py
│   ├── services/
│   │   └── table_services.py
│   └── table_extraction_use_case.py
├── adaptors/
│   └── table_extraction_ports.py
├── frameworks/
│   ├── ocr_service.py
│   ├── pdf_image_extractor.py
│   ├── table_extraction_factory.py
│   ├── table_structure_recognizer.py
│   └── table_transformer_detector.py
```

## Architecture Layers

### 1. Entities Layer (`table_rag/entities/`)
- **table_entities.py**: Core business entities and domain services
  - `BoundingBox`: Value object for coordinates
  - `DetectedCell`: Detected table cell entity
  - `GridCell`: Structured grid cell entity  
  - `TableGrid`: Complete table structure entity
  - `DetectedTable`: Detected table with metadata
  - `PageImage`: PDF page image entity

### 2. Use Cases Layer (`table_rag/usecases/`)
- **table_extraction_use_case.py**: Application business logic
  - `TableExtractionUseCase`: Orchestrates table extraction workflow
  - `TableGridBuilder`: Builds structured grids from detected cells
  - Contains the core algorithms for grouping rows/columns and building grids
- **services/table_services.py**: Supporting services for use cases
  - `TableValidationService`: Validates detected table structures and cells
  - `CoordinateClusteringService`: Clusters coordinates for row/column grouping
- **dtos.py**: Data transfer objects for use cases
  - `TableExtractionRequest`: Request DTO for table extraction
  - `TableExtractionResponse`: Response DTO for table extraction

### 3. Interface Adapters Layer (`table_rag/adaptors/`)
- **table_extraction_ports.py**: Abstract interfaces and DTOs
  - Port interfaces: `PDFImageExtractorPort`, `TableDetectorPort`, etc.
  - `TableExtractionAdapter`: Coordinates between use cases and external interfaces

### 4. Frameworks & Drivers Layer (`table_rag/frameworks/`)
- **pdf_image_extractor.py**: PyMuPDF implementation
- **table_transformer_detector.py**: Table detection using Transformer models
- **table_structure_recognizer.py**: Structure recognition using Transformer models
- **ocr_service.py**: TrOCR text extraction
- **table_extraction_factory.py**: Dependency injection and configuration


### Usage (Simple)
```python
from table_rag.frameworks.table_extraction_factory import TableExtractionService

service = TableExtractionService(device="cpu")
result = service.extract_tables_from_page(pdf_path, page_number)
tables = result["tables"]
```

### Usage (Advanced)
```python
from table_rag.frameworks.table_extraction_factory import TableExtractionFactory
from table_rag.usecases.dtos import TableExtractionRequest

# Create with custom configuration
adapter = TableExtractionFactory.create_table_extraction_adapter(
    device="cuda",
    detection_threshold=0.95,
    structure_threshold=0.7
)

# Use the adapter
request = TableExtractionRequest(pdf_path, page_number)
response = adapter.extract_tables(request)
```
