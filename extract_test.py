import fitz
import sys

def main():
    doc = fitz.open("DOC-20260613-WA0000..pdf")
    page = doc[1] # Look at page 2 (index 1) which has names
    blocks = page.get_text("dict")["blocks"]
    for b in blocks:
        if "lines" in b:
            for l in b["lines"]:
                for s in l["spans"]:
                    # Print the first few strings that are in Telugu (we know Gautami is used)
                    if "Gautami" in s["font"]:
                        print(f"Font: {s['font']}, Text: {repr(s['text'])}, Origin: {s['origin']}")
                        
if __name__ == "__main__":
    main()
