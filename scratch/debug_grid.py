import cv2
import fitz
import numpy as np

doc = fitz.open("DOC-20260613-WA0000..pdf")
page = doc[2] # Page 3
pix = page.get_pixmap(dpi=200)
img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
if pix.n == 4:
    img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)

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
    cells.append((x, y, w, h))

print(f"Total contours found: {len(cells)}")

valid_cells = []
for x, y, w, h in cells:
    if w > 100 and h > 50 and w < 1000 and h < 500:
        valid_cells.append((x, y, w, h))

print(f"Valid cells found: {len(valid_cells)}")
for c in valid_cells[:5]:
    print(c)
