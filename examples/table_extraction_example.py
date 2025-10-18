from pdf2table.frameworks.pipeline import create_pipeline

# Create the extraction pipeline with configuration
pipeline = create_pipeline(
    device="cpu",
    detection_threshold=0.9,
    structure_threshold=0.6,
    pdf_dpi=300,
    load_ocr=False,
    visualize=False
)

pdf_path = "tests/samples/oxford-textbook-of-medicine-693.pdf"

# Extract tables from a specific page
response = pipeline.extract_tables(pdf_path=pdf_path, page_number=0)

# Or extract tables from all pages
# response = pipeline.extract_tables(pdf_path=pdf_path)

# Check if extraction was successful
if response.success:
    print(f"Successfully extracted {len(response.tables)} tables")
    
    # Access extracted tables
    for table in response.tables:
        print(f"Table with {len(table.grid.cells)} cells")
        print(f"Grid size: {table.grid.n_rows} x {table.grid.n_cols}")
    
    # Convert to dictionary format
    result_dict = response.to_dict()
    print(result_dict)
    
    # Save results to JSON file
    response.save_to_json("data/extracted_tables.json")
else:
    print(f"Extraction failed: {response.error_message}")