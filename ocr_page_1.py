import fitz
import easyocr
import numpy as np
import cv2

def main():
    print("Loading EasyOCR...")
    reader = easyocr.Reader(['te', 'en'], gpu=False)
    
    doc = fitz.open("DOC-20260613-WA0000..pdf")
    page = doc[0] # Page 1 (index 0)
    
    # Render at 300 DPI
    pix = page.get_pixmap(dpi=300)
    img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
    if pix.n == 4:
        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
        
    print("Running OCR on Page 1...")
    results = reader.readtext(img_array)
    
    print("--- PAGE 1 TEXT ---")
    for bbox, text, prob in results:
        print(text)

if __name__ == "__main__":
    main()
