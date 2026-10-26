#!/usr/bin/env python3
"""OCR all *_via_cdp.pdf 990s to same-basename .txt (200 DPI + tesseract)."""
import glob
import os
import subprocess
import tempfile

import pypdfium2 as pdfium

CACHE = os.path.dirname(os.path.abspath(__file__))


def ocr_pdf(pdf_path):
    txt_path = os.path.splitext(pdf_path)[0] + '.txt'
    if os.path.exists(txt_path) and os.path.getsize(txt_path) > 0:
        print('SKIP (has txt): ' + os.path.basename(pdf_path), flush=True)
        return txt_path
    print('OCR: ' + os.path.basename(pdf_path), flush=True)
    pdf = pdfium.PdfDocument(pdf_path)
    tmpdir = tempfile.gettempdir()
    with open(txt_path, 'w', encoding='utf-8') as out:
        for i in range(len(pdf)):
            img = os.path.join(tmpdir, 'ocr_pg.png')
            pdf[i].render(scale=200 / 72).to_pil().save(img)
            r = subprocess.run(['tesseract', img, 'stdout'],
                               capture_output=True, text=True, timeout=300)
            out.write('\n\f=== PAGE %d ===\n' % (i + 1))
            out.write(r.stdout or '')
            print('  page %d/%d' % (i + 1, len(pdf)), flush=True)
    print('WROTE: ' + txt_path, flush=True)
    return txt_path


if __name__ == '__main__':
    pdfs = sorted(glob.glob(os.path.join(CACHE, '*_via_cdp.pdf')))
    print('%d PDFs' % len(pdfs), flush=True)
    for p in pdfs:
        ocr_pdf(p)
    print('OCR ALL DONE', flush=True)
