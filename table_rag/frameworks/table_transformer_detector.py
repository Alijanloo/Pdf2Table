import torch
from typing import List
from transformers import DetrFeatureExtractor, TableTransformerForObjectDetection

from table_rag.entities.table_entities import PageImage, DetectedTable, BoundingBox
from table_rag.adaptors.table_extraction_adaptor import TableDetectorInterface


class TableTransformerDetector(TableDetectorInterface):
    """Concrete implementation of table detection using Microsoft Table Transformer."""
    
    def __init__(
        self, 
        model_name: str = "microsoft/table-transformer-detection",
        device: str = "cpu",
        confidence_threshold: float = 0.9
    ):
        self.model = TableTransformerForObjectDetection.from_pretrained(model_name)
        self.feature_extractor = DetrFeatureExtractor.from_pretrained(model_name)
        self.device = device
        self.confidence_threshold = confidence_threshold
        
        self.model.to(self.device)
        self.model.eval()
    
    def detect_tables(self, page_image: PageImage) -> List[DetectedTable]:
        """Detect tables in a page image using Table Transformer."""
        try:
            # Prepare input
            encoding = self.feature_extractor(
                images=page_image.image_data, 
                return_tensors="pt"
            )
            
            # Move to device
            for k, v in encoding.items():
                encoding[k] = v.to(self.device)
            
            # Run inference
            with torch.no_grad():
                outputs = self.model(**encoding)
            
            # Post-process results
            results = self.feature_extractor.post_process_object_detection(
                outputs,
                threshold=self.confidence_threshold,
                target_sizes=[page_image.dimensions],
            )[0]
            
            # Convert to domain objects
            detected_tables = []
            for score, label, box in zip(
                results["scores"], 
                results["labels"], 
                results["boxes"]
            ):
                box_coords = [round(i) for i in box.tolist()]
                
                detection_box = BoundingBox(
                    x_min=box_coords[0],
                    y_min=box_coords[1],
                    x_max=box_coords[2],
                    y_max=box_coords[3]
                )
                
                detected_table = DetectedTable(
                    detection_box=detection_box,
                    confidence_score=score.item(),
                    page_number=page_image.page_number,
                    source_file=page_image.source_file
                )
                
                detected_tables.append(detected_table)
            
            return detected_tables
            
        except Exception as e:
            raise RuntimeError(f"Table detection failed: {str(e)}")
    
    def set_confidence_threshold(self, threshold: float):
        """Update confidence threshold."""
        if not 0 <= threshold <= 1:
            raise ValueError("Confidence threshold must be between 0 and 1")
        self.confidence_threshold = threshold
