import fitz
from fontTools.ttLib import TTFont

def main():
    font = TTFont("ABCDEE+Gautami.ttf")
    cmap = font['cmap'].getBestCmap()
    gid_to_unicode = {}
    
    for u, gname in cmap.items():
        gid = font.getGlyphID(gname)
        gid_to_unicode[gid] = chr(u)
        
    doc = fitz.open("DOC-20260613-WA0000..pdf")
    page = doc[1]
    
    blocks = page.get_text("dict")["blocks"]
    count = 0
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
                        count += 1
                        if count > 20:
                            return

if __name__ == "__main__":
    main()
