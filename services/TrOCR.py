from transformers import TrOCRProcessor, VisionEncoderDecoderModel
import torch
from PIL import Image
from .Gray import clean_captcha
import time
import os
if "HF_HOME" not in os.environ:
    os.environ["HF_HOME"] = os.getcwd()
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Global variables for lazy loading
_processor = None
_model = None
_model_load_attempted = False

def _load_model_with_retry(max_retries=3, delay=2):
    """Load the TrOCR model with retry logic for Cloud Run"""
    global _processor, _model, _model_load_attempted
    
    if _processor is not None and _model is not None:
        return _processor, _model
    
    if _model_load_attempted:
        # Already failed, don't retry
        raise RuntimeError("Model loading previously failed")
    
    for attempt in range(max_retries):
        try:
            print(f"Loading TrOCR model (attempt {attempt + 1}/{max_retries})...")
            _processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-stage1")
            _model = VisionEncoderDecoderModel.from_pretrained(
                "microsoft/trocr-base-stage1",
                device_map=None,          # disables meta
                torch_dtype=torch.float32
            )
            _model.to("cpu")
            _model.eval()
            print("TrOCR model loaded successfully!")
            return _processor, _model
        except Exception as e:
            print(f"Failed to load model (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                _model_load_attempted = True
                raise RuntimeError(f"Failed to load TrOCR model after {max_retries} attempts: {e}")


def run_ocr(img):
    """Run OCR on the image using TrOCR model (loaded lazily on first use)"""
    start = time.time()
    
    # Load model on first use
    processor, model = _load_model_with_retry()
    
    ENABLE_CLEAN = True
    if ENABLE_CLEAN:
        cleaned = clean_captcha(img)
    else:
        cleaned = img

    # --- FIX: ensure RGB PIL image ---
    if not isinstance(cleaned, Image.Image):
        cleaned = Image.fromarray(cleaned)

    if cleaned.mode != "RGB":
        cleaned = cleaned.convert("RGB")
    # ----------------------------------

    pixel_values = processor(images=cleaned, return_tensors="pt").pixel_values
    output_ids = model.generate(pixel_values, max_length=10)
    text = processor.batch_decode(output_ids, skip_special_tokens=True)[0]

    print("Time:", time.time() - start)
    ctext = text.replace(".", "")
    cap_text = "".join((ctext.split()))
    return cap_text


if __name__ == "__main__":
    img = Image.open("../captcha.jpg").convert("RGB")
    text = run_ocr(img)
    print(text)