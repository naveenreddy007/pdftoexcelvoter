import fitz
import sys

def main():
    doc = fitz.open("DOC-20260613-WA0000..pdf")
    for page_num in range(min(5, doc.page_count)):
        font_list = doc.get_page_fonts(page_num)
        for font in font_list:
            xref = font[0]
            name = font[3]
            if "Gautami" in name:
                print(f"Extracting font {name} with xref {xref}")
                # Try to extract font buffer
                try:
                    font_buffer = doc.extract_font(xref)
                    with open(f"{name}.ttf", "wb") as f:
                        f.write(font_buffer[3])
                    print(f"Saved {name}.ttf")
                except Exception as e:
                    print(f"Failed to extract {name}: {e}")
                    
if __name__ == "__main__":
    main()
