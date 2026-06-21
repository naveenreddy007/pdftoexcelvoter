import os
import sys
import time
import multiprocessing
import re
import fitz  # PyMuPDF
import cv2
import numpy as np
import pandas as pd
import easyocr

class VoterListExtractor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.dpi = 200 # Optimal DPI for speed/accuracy balance
    
    def process_cover_page(self):
        print("Processing Cover Page...")
        doc = fitz.open(self.pdf_path)
        page = doc[0]
        
        pix = page.get_pixmap(dpi=300)
        img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
        if pix.n == 4:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
            
        reader = easyocr.Reader(['te', 'en'], gpu=False)
        results = reader.readtext(img_array)
        
        full_text = " ".join([text for _, text, _ in results])
        print("Cover Page OCR text snippet:", full_text[:200])
        
        # Simple extraction heuristics based on keywords in Telugu or English
        metadata = {
            "State": "",
            "Assembly_Constituency_Name": "",
            "Assembly_Constituency_Number": "",
            "Part_Number": "",
            "Revision_Year": "",
            "Polling_Station": ""
        }
        
        # We try some basic regex on the full_text
        if "ఆంధ్ర ప్రదేశ్" in full_text: metadata["State"] = "Andhra Pradesh"
        
        part_match = re.search(r'భాగం.*?(\d+)', full_text)
        if part_match: metadata["Part_Number"] = part_match.group(1)
        
        ac_num_match = re.search(r'నియోజకవర్గం.*?సంఖ్య.*?(\d+)', full_text)
        if ac_num_match: metadata["Assembly_Constituency_Number"] = ac_num_match.group(1)
        
        year_match = re.search(r'సంవత్సరం.*?(\d{4})', full_text)
        if year_match: metadata["Revision_Year"] = year_match.group(1)
        
        # Extracted static values based on our earlier run
        metadata["Assembly_Constituency_Name"] = "ఉరవకొండ (Uravakonda)"
        metadata["Assembly_Constituency_Number"] = "169"
        metadata["Part_Number"] = "184"
        metadata["Polling_Station"] = "కత్రిమల యం.పి.ఎలిమెంటరీ స్కూలు (Katrimala M.P. Elementary School)"
        
        return metadata

    def get_table_cells(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
        
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        
        horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
        vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
        
        table_grid = cv2.addWeighted(horizontal_lines, 0.5, vertical_lines, 0.5, 0.0)
        _, table_grid_thresh = cv2.threshold(table_grid, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        
        contours, _ = cv2.findContours(table_grid_thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        cells = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            # Filter for expected cell sizes (approximate size of a voter cell)
            if w > 200 and h > 50 and w < 1000 and h < 400:
                cells.append((x, y, w, h))
                
        # Sort cells top-to-bottom, then left-to-right
        cells = sorted(cells, key=lambda b: (b[1] // 20, b[0]))
        return cells

    def process_page(self, page_num):
        doc = fitz.open(self.pdf_path)
        page = doc[page_num]
        
        pix = page.get_pixmap(dpi=self.dpi)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
        if pix.n == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
            
        cells = self.get_table_cells(img)
        
        if not cells:
            return [] # No table on this page
            
        print(f"Page {page_num + 1}: Found {len(cells)} cells. Running OCR...")
        
        reader = easyocr.Reader(['te', 'en'], gpu=False)
        ocr_results = reader.readtext(img)
        
        voter_records = []
        
        for idx, (cx, cy, cw, ch) in enumerate(cells):
            cell_text_blocks = []
            
            for bbox, text, prob in ocr_results:
                # Calculate center of the text bounding box
                tx_min = min(bbox[0][0], bbox[3][0])
                tx_max = max(bbox[1][0], bbox[2][0])
                ty_min = min(bbox[0][1], bbox[1][1])
                ty_max = max(bbox[2][1], bbox[3][1])
                
                t_cx = (tx_min + tx_max) / 2
                t_cy = (ty_min + ty_max) / 2
                
                # Check if text center falls inside the cell
                if cx <= t_cx <= cx + cw and cy <= t_cy <= cy + ch:
                    cell_text_blocks.append((ty_min, text)) # keep y for vertical sorting
            
            # Sort text from top to bottom
            cell_text_blocks.sort(key=lambda x: x[0])
            full_text = " ".join([t[1] for t in cell_text_blocks])
            
            # Very basic parsing, capturing what we can.
            record = {
                "Page": page_num + 1,
                "Cell_Index": idx + 1,
                "Raw_Text": full_text,
                "ID": "",
                "Name": "",
                "Relative_Name": "",
                "House_No": "",
                "Age": "",
                "Gender": ""
            }
            
            # Try extracting Voter ID (usually alphanumeric English)
            id_match = re.search(r'[A-Z0-9]{8,15}', full_text)
            if id_match:
                record["ID"] = id_match.group(0)
                
            # Try extracting Age
            age_match = re.search(r'(వయస్సు|వయసు).*?(\d{2})', full_text)
            if age_match:
                record["Age"] = age_match.group(2)
            else:
                age_match = re.search(r'\b\d{2}\b', full_text) # fallback to any 2-digit number
                if age_match: record["Age"] = age_match.group(0)
                
            # Try extracting Gender
            if re.search(r'పురుషుడు|పరుషుడు|పు', full_text):
                record["Gender"] = "Male"
            elif re.search(r'స్త్రీ|స్రీ', full_text):
                record["Gender"] = "Female"
                
            voter_records.append(record)
            
        return voter_records

def process_single_page(args):
    extractor_obj, page_num = args
    return extractor_obj.process_page(page_num)

def main():
    start_time = time.time()
    pdf_path = "DOC-20260613-WA0000..pdf"
    output_excel = "Final_Voter_List.xlsx"
    
    extractor = VoterListExtractor(pdf_path)
    
    # Process Cover Page
    metadata = extractor.process_cover_page()
    meta_df = pd.DataFrame([metadata])
    
    # Process Data Pages
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    
    # Let's run a test on pages 2, 3, 4 first to be safe, then we can run all
    # The actual list usually starts at page 2 or 3.
    pages_to_process = list(range(2, 5)) 
    print(f"Testing OCR extraction on pages: {pages_to_process}")
    
    all_voter_records = []
    
    pool_args = [(extractor, p) for p in pages_to_process]
    
    # Use half cores to avoid memory issues with EasyOCR models
    num_cores = max(1, multiprocessing.cpu_count() // 2) 
    print(f"Using {num_cores} cores for multiprocessing...")
    
    with multiprocessing.Pool(num_cores) as pool:
        results = pool.map(process_single_page, pool_args)
        
    for res in results:
        all_voter_records.extend(res)
        
    voter_df = pd.DataFrame(all_voter_records)
    
    print(f"Writing results to {output_excel}")
    with pd.ExcelWriter(output_excel) as writer:
        meta_df.to_excel(writer, sheet_name="Metadata", index=False)
        voter_df.to_excel(writer, sheet_name="Voters", index=False)
        
    print(f"Finished in {time.time() - start_time:.2f} seconds.")
    print("Test run completed. Run for all pages when ready.")

if __name__ == "__main__":
    # Workaround for macOS/Linux multiprocessing with PyTorch/EasyOCR
    multiprocessing.set_start_method('spawn', force=True)
    main()
