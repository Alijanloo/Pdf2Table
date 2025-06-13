import torch
import numpy as np
from typing import List
from transformers import DetrFeatureExtractor, TableTransformerForObjectDetection

from table_rag.entities.table_entities import PageImage, DetectedCell, BoundingBox
from table_rag.usecases.interfaces.framework_interfaces import TableStructureRecognizerInterface


class TableTransformerStructureRecognizer(TableStructureRecognizerInterface):
    """Concrete implementation of table structure recognition using Microsoft Table Transformer."""
    
    def __init__(
        self,
        model_name: str = "microsoft/table-transformer-structure-recognition-v1.1-all",
        device: str = "cpu",
        confidence_threshold: float = 0.6
    ):
        self.model = TableTransformerForObjectDetection.from_pretrained(model_name)
        self.feature_extractor = DetrFeatureExtractor.from_pretrained(model_name)
        self.feature_extractor.size["shortest_edge"] = 800
        
        self.device = device
        self.confidence_threshold = confidence_threshold
        
        self.model.to(self.device)
        self.model.eval()
        
        # Relevant cell types for table structure
        self.relevant_cell_types = {
            "table column",
            "table row", 
            "table column header",
            "table projected row header",
            "table spanning cell"
        }
    
    def recognize_structure(self, page_image: PageImage, table_box: BoundingBox) -> List[DetectedCell]:
        """Recognize structure of a detected table."""
        try:
            # Crop table region from page image
            table_image = self._crop_table_image(page_image.image_data, table_box)
            
            # Prepare input
            encoding = self.feature_extractor(
                images=table_image,
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
                target_sizes=[(table_image.shape[0], table_image.shape[1])],
            )[0]
            
            # Convert to domain objects
            detected_cells = []
            for score, label, box in zip(
                results["scores"], 
                results["labels"], 
                results["boxes"]
            ):
                label_name = self.model.config.id2label[label.item()]
                
                # Only process relevant cell types
                if label_name in self.relevant_cell_types:
                    box_coords = [round(i) for i in box.tolist()]
                    
                    # Convert relative coordinates to absolute coordinates
                    abs_box = BoundingBox(
                        x_min=box_coords[0] + table_box.x_min,
                        y_min=box_coords[1] + table_box.y_min,
                        x_max=box_coords[2] + table_box.x_min,
                        y_max=box_coords[3] + table_box.y_min
                    )
                    
                    # Extract cell image crop
                    cell_crop = table_image[
                        box_coords[1]:box_coords[3], 
                        box_coords[0]:box_coords[2]
                    ]
                    
                    detected_cell = DetectedCell(
                        box=abs_box,
                        cell_type=label_name,
                        confidence_score=score.item(),
                        image_crop=cell_crop
                    )
                    
                    detected_cells.append(detected_cell)
            
            return detected_cells
            
        except Exception as e:
            raise RuntimeError(f"Table structure recognition failed: {str(e)}")
    
    def _crop_table_image(self, page_image: np.ndarray, table_box: BoundingBox) -> np.ndarray:
        """Crop table region from page image."""
        try:
            # Ensure coordinates are within image bounds
            y_min = max(0, table_box.y_min)
            y_max = min(page_image.shape[0], table_box.y_max)
            x_min = max(0, table_box.x_min)
            x_max = min(page_image.shape[1], table_box.x_max)
            
            # Crop the image
            cropped = page_image[y_min:y_max, x_min:x_max]
            
            if cropped.size == 0:
                raise ValueError("Cropped table image is empty")
            
            return cropped
            
        except Exception as e:
            raise RuntimeError(f"Failed to crop table image: {str(e)}")
    
    def set_confidence_threshold(self, threshold: float):
        """Update confidence threshold."""
        if not 0 <= threshold <= 1:
            raise ValueError("Confidence threshold must be between 0 and 1")
        self.confidence_threshold = threshold
