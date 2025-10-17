# Table Extraction Module

## Directory Structure
```
pdf2table/
├── entities/
│   └── table_entities.py
├── usecases/
│   ├── services/
│   │   └── table_services.py
│   ├── interfaces/
│   └── table_extraction_use_case.py
├── frameworks/
│   ├── ocr_service.py
│   ├── pdf_image_extractor.py
│   ├── pipeline.py
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
    - Returns list of `DetectedTable` objects
  - `TableGridBuilder`: Builds structured grids from detected cells
  - Contains the core algorithms for grouping rows/columns and building grids
- **services/table_services.py**: Supporting services for use cases
  - `TableValidationService`: Validates detected table structures and cells
  - `CoordinateClusteringService`: Clusters coordinates for row/column grouping
- **interfaces/**: Port interfaces for dependency inversion

### 3. Frameworks & Drivers Layer (`pdf2table/frameworks/`)
- **pdf_image_extractor.py**: PyMuPDF implementation
- **table_transformer_detector.py**: Table detection using Transformer models
- **table_structure_recognizer.py**: Structure recognition using Transformer models
- **ocr_service.py**: TrOCR text extraction
- **pipeline.py**: Factory for creating configured pipelines

## Usage

```python
from pdf2table.frameworks.pipeline import create_pipeline

# Create the extraction pipeline
use_case = create_pipeline(
    device="cpu",
    detection_threshold=0.9,
    structure_threshold=0.6,
    pdf_dpi=300,
    load_ocr=False,
    visualize=False
)

# Extract from a specific page
tables = use_case.extract_tables(pdf_path, page_number=0)

# Or extract from all pages
all_tables = use_case.extract_tables(pdf_path)

# Process the results
for table in tables:
    print(f"Found table with {table.grid.n_rows} rows and {table.grid.n_cols} columns")
    table_dict = table.to_dict()
```
