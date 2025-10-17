# Table Extraction Module

## Directory Structure
```
pdf2table/
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

### 1. Entities Layer (`pdf2table/entities/`)
- **table_entities.py**: Core business entities and domain services
  - `BoundingBox`: Value object for coordinates
  - `DetectedCell`: Detected table cell entity
  - `GridCell`: Structured grid cell entity  
  - `TableGrid`: Complete table structure entity
  - `DetectedTable`: Detected table with metadata
  - `PageImage`: PDF page image entity

### 2. Use Cases Layer (`pdf2table/usecases/`)
- **table_extraction_use_case.py**: Application business logic
  - `TableExtractionUseCase`: Orchestrates table extraction workflow
    - `extract_tables(pdf_path, page_number=None)`: Main extraction method
  - `TableGridBuilder`: Builds structured grids from detected cells
  - Contains the core algorithms for grouping rows/columns and building grids
- **services/table_services.py**: Supporting services for use cases
  - `TableValidationService`: Validates detected table structures and cells
  - `CoordinateClusteringService`: Clusters coordinates for row/column grouping
- **dtos.py**: Data transfer objects for use cases
  - `TableExtractionResponse`: Response DTO for table extraction

### 3. Interface Adapters Layer (`pdf2table/adaptors/`)
- **table_extraction_adaptor.py**: Adapter for table extraction
  - `TableExtractionAdapter`: Coordinates between use cases and external interfaces
    - `extract_tables(pdf_path, page_number=None)`: Main adapter method
      - Accepts `pdf_path` and optional `page_number`
      - Returns `TableExtractionResponse`

### 4. Frameworks & Drivers Layer (`pdf2table/frameworks/`)
- **pdf_image_extractor.py**: PyMuPDF implementation
- **table_transformer_detector.py**: Table detection using Transformer models
- **table_structure_recognizer.py**: Structure recognition using Transformer models
- **ocr_service.py**: TrOCR text extraction
- **table_extraction_factory.py**: Dependency injection and configuration


### Usage (Simple)
```python
from pdf2table.frameworks.table_extraction_factory import TableExtractionService

service = TableExtractionService(device="cpu")

# Extract from a specific page
result = service.extract_tables_from_page(pdf_path, page_number=0)
tables = result["tables"]

# Or extract from all pages
all_results = service.extract_tables_from_pdf(pdf_path)
```

### Usage (Advanced)
```python
from pdf2table.frameworks.table_extraction_factory import TableExtractionFactory

# Create with custom configuration
adapter = TableExtractionFactory.create_table_extraction_adapter(
    device="cuda",
    detection_threshold=0.95,
    structure_threshold=0.7
)

# Extract from a specific page
response = adapter.extract_tables(pdf_path, page_number=0)

# Or extract from all pages
response = adapter.extract_tables(pdf_path)
```
