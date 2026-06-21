import fitz
from fontTools.ttLib import TTFont

def main():
    # Load the reversed cmap
    font = TTFont("ABCDEE+Gautami.ttf")
    cmap = font['cmap'].getBestCmap()
    gid_to_unicode = {}
    glyph_order = font.getGlyphOrder()
    
    for u, gname in cmap.items():
        gid = font.getGlyphID(gname)
        gid_to_unicode[gid] = chr(u)
        
    print(f"Total glyphs in font: {len(glyph_order)}")
    print(f"Glyphs mapped to Unicode: {len(gid_to_unicode)}")
    
    # Extract raw text from PyMuPDF
    doc = fitz.open("DOC-20260613-WA0000..pdf")
    page = doc[1]
    
    # We can get the raw text bytes by inspecting the dict, but PyMuPDF's get_text
    # gives characters. For Identity-H, the characters returned are actually the CIDs mapped to chr()
    # Let's verify by printing the ord() of the first few characters.
    
    blocks = page.get_text("dict")["blocks"]
    for b in blocks:
        if "lines" in b:
            for l in b["lines"]:
                for s in l["spans"]:
                    if "Gautami" in s["font"]:
                        text = s["text"]
                        decoded = ""
                        for char in text:
                            cid = ord(char)
                            if cid in gid_to_unicode:
                                decoded += gid_to_unicode[cid]
                            else:
                                decoded += f"[GID:{cid}]"
                        print(f"Raw: {repr(text)} -> Decoded: {decoded}")
                        return # just test the first one

if __name__ == "__main__":
    main()
