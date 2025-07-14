import torch
import cv2
import numpy as np
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

from pdf2table.usecases.interfaces.framework_interfaces import OCRInterface


class TrOCRService(OCRInterface):
    """Concrete implementation of OCR using Microsoft TrOCR."""
    
    def __init__(
        self,
        model_name: str = "microsoft/trocr-base-printed",
        device: str = "cpu"
    ):
        self.processor = TrOCRProcessor.from_pretrained(model_name)
        self.model = VisionEncoderDecoderModel.from_pretrained(model_name)
        self.device = device
        
        self.model.to(self.device)
        self.model.eval()
    
    def extract_text(self, image_crop: np.ndarray) -> str:
        """Extract text from image crop using TrOCR."""
        try:
            if image_crop.size == 0 or image_crop.shape[0] == 0 or image_crop.shape[1] == 0:
                return ""
            
            # Convert BGR to RGB if necessary
            if len(image_crop.shape) == 3 and image_crop.shape[2] == 3:
                # Assume it's BGR, convert to RGB
                rgb_image = cv2.cvtColor(image_crop, cv2.COLOR_BGR2RGB)
            else:
                rgb_image = image_crop
            
            # Convert to PIL Image
            pil_image = Image.fromarray(rgb_image)
            
            # Process with TrOCR
            pixel_values = self.processor(
                images=pil_image, 
                return_tensors="pt"
            ).pixel_values.to(self.device)
            
            # Generate text
            with torch.no_grad():
                generated_ids = self.model.generate(pixel_values)
            
            # Decode text
            generated_text = self.processor.batch_decode(
                generated_ids, 
                skip_special_tokens=True
            )[0]
            
            return generated_text.strip()
            
        except Exception as e:
            # Log error but don't fail - return empty string
            print(f"OCR extraction failed: {str(e)}")
            return ""
    
    def extract_text_batch(self, image_crops: list[np.ndarray]) -> list[str]:
        """Extract text from multiple image crops in batch."""
        results = []
        for crop in image_crops:
            results.append(self.extract_text(crop))
        return results
