import fitz
import easyocr
import pandas as pd
import numpy as np

def extract_page(page_num, pdf_path, reader):
    print(f"Processing page {page_num}...")
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    
    # Render page to an image
    pix = page.get_pixmap(dpi=300)
    img_data = pix.tobytes("png")
    
    # Run EasyOCR
    # Note: Using tel (Telugu) and en (English) for numbers
    results = reader.readtext(img_data)
    
    # A simple heuristic to sort results top-to-bottom, left-to-right
    # In reality, tabular extraction requires careful bounding box alignment
    data = []
    for (bbox, text, prob) in results:
        # bbox is [top-left, top-right, bottom-right, bottom-left]
        y = bbox[0][1]
        x = bbox[0][0]
        data.append((y, x, text, prob))
        
    data.sort(key=lambda item: (item[0] // 20, item[1])) # Group by roughly same Y (line), then X
    
    return data

def main():
    print("Loading EasyOCR model for Telugu and English...")
    # Initialize reader
    reader = easyocr.Reader(['te', 'en'])
    
    pdf_path = "DOC-20260613-WA0000..pdf"
    
    # Extract only page 2 (index 1) for a quick test
    data = extract_page(1, pdf_path, reader)
    
    # For now, just save raw data to see if Telugu text comes out properly
    df = pd.DataFrame(data, columns=["Y", "X", "Text", "Confidence"])
    excel_path = "test_output.xlsx"
    df.to_excel(excel_path, index=False)
    print(f"Saved raw OCR results to {excel_path}")

if __name__ == "__main__":
    main()
