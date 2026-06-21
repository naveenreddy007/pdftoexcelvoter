from fontTools.ttLib import TTFont
import sys

def main():
    font = TTFont("ABCDEE+Gautami.ttf")
    print("Tables in font:", font.keys())
    
    if 'cmap' in font:
        cmap = font['cmap'].getBestCmap()
        print(f"Cmap contains {len(cmap)} entries.")
        # Print a few mappings
        for k, v in list(cmap.items())[:20]:
            print(f"Unicode: {k} (0x{k:04x}) -> Glyph name: {v}")
    else:
        print("No cmap table found!")

if __name__ == "__main__":
    main()
