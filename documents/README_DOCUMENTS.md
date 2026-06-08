# About these documents

This folder is the corpus for The Unofficial Guide. The pipeline (`ingest.py`)
automatically loads every `.txt` and `.pdf` file here, so **adding real documents
is just dropping files in and re-running `python embed_store.py`.**

## ⚠️ These are SAMPLE documents

The 13 files here are **realistic sample data** written to mimic the structure of
real student-generated knowledge (Rate My Professors reviews, r/berkeley threads,
a Discord advice channel). They were created because Reddit and Rate My Professors
**block automated scraping** (they require JavaScript rendering and return 403 to
bots), so the corpus could not be auto-collected in this environment — exactly the
scraping difficulty the project brief anticipates.

They let the system run, retrieve, generate, and be evaluated end-to-end today.

## To submit with REAL collected documents

The brief explicitly says manual copy-paste is normal and expected. To swap in real
content:

1. Open a real thread (e.g. an r/berkeley thread, a Rate My Professors page).
2. Copy the post + comments into a new `.txt` file in this folder. Keep the same
   light header format if you like:
   ```
   SOURCE: <url or description>
   COLLECTED: <date>

   <pasted content>
   ```
   (The `SOURCE:`/`COLLECTED:` header lines are stripped automatically during
   cleaning — they're just provenance notes for you.)
3. Delete the sample files you're replacing.
4. Re-run `python embed_store.py` to rebuild the index, then `python evaluate.py`.

PDFs (housing handbooks, syllabi) also work — `ingest.py` reads them with
pdfplumber (digitally-created PDFs only; no OCR for scanned images).
