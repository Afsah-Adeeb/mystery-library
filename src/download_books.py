"""
Step 0: Download the book corpus from Project Gutenberg.

WHY A SCRIPT AND NOT A FOLDER OF FILES
----------------------------------------
The corpus is part of the experiment. Every number in eval/ (hit rate, the
refusal threshold, the random baseline) is only true for THIS set of books,
so the set has to be reproducible: anyone can re-run this script and get the
same 23 texts, byte for byte, from the same source.

WHY THESE BOOKS
-----------------
Classic mystery fiction, because a detective story is full of small, checkable
facts (who, where, what weapon, what clue) -- exactly what a RAG evaluation
needs. A question like "What breed was the dog in Silver Blaze?" has one right
answer that either is or is not in the retrieved text.

Every author here died before 1950, so the books are public domain in the
US, the UK and India, not just one of them. That rule is why Agatha Christie
is NOT here: her early novels are public domain in the US, but she died in
1976, so they stay under copyright in India and the UK.

The full Sherlock Holmes canon (9 books) is in on purpose. Sixty stories with
the same detective, the same narrator and the same flat in Baker Street make
retrieval HARD: many passages look alike, so the search has to find the one
story that actually answers. That is a better test than nine unrelated books.

WHERE THE FILES COME FROM
---------------------------
gutenberg.pglaf.org is an official Project Gutenberg mirror. The main site
asks automated downloaders to use mirrors rather than www.gutenberg.org, and
the main site was down for maintenance when this corpus was built anyway.
Files are saved exactly as downloaded (licence header included); ingest.py
strips the Gutenberg header and footer when it reads them.
"""

import json
import time
import urllib.request

import config

MIRROR_URL = "https://gutenberg.pglaf.org/cache/epub/{id}/pg{id}.txt"

# (Gutenberg ID, title used as the file name, author, year first published)
BOOKS = [
    # Sherlock Holmes -- the complete canon: 4 novels + 5 story collections
    (244,   "A Study in Scarlet",                      "Arthur Conan Doyle", 1887),
    (2097,  "The Sign of the Four",                    "Arthur Conan Doyle", 1890),
    (1661,  "The Adventures of Sherlock Holmes",       "Arthur Conan Doyle", 1892),
    (834,   "The Memoirs of Sherlock Holmes",          "Arthur Conan Doyle", 1894),
    (2852,  "The Hound of the Baskervilles",           "Arthur Conan Doyle", 1902),
    (108,   "The Return of Sherlock Holmes",           "Arthur Conan Doyle", 1905),
    (3289,  "The Valley of Fear",                      "Arthur Conan Doyle", 1915),
    (2350,  "His Last Bow",                            "Arthur Conan Doyle", 1917),
    (69700, "The Case-Book of Sherlock Holmes",        "Arthur Conan Doyle", 1927),
    # Father Brown
    (204,   "The Innocence of Father Brown",           "G. K. Chesterton", 1911),
    (223,   "The Wisdom of Father Brown",              "G. K. Chesterton", 1914),
    # The founders of the genre
    # The Raven Edition (1903) of tales that Poe first collected in his
    # "Tales" of 1845 -- dated 1845 so the shelf puts the genre's inventor
    # first. Volume 1 has the first detective story ever written, "The
    # Murders in the Rue Morgue" (1841).
    (2147,  "The Works of Edgar Allan Poe, Volume 1",  "Edgar Allan Poe", 1845),
    (2148,  "The Works of Edgar Allan Poe, Volume 2",  "Edgar Allan Poe", 1845),
    (155,   "The Moonstone",                           "Wilkie Collins", 1868),
    (564,   "The Mystery of Edwin Drood",              "Charles Dickens", 1870),
    (4047,  "The Leavenworth Case",                    "Anna Katharine Green", 1878),
    # Locked rooms, armchair detectives and gentleman thieves
    (28164, "The Big Bow Mystery",                     "Israel Zangwill", 1892),
    (706,   "The Amateur Cracksman",                   "E. W. Hornung", 1899),
    (1685,  "The Mystery of the Yellow Room",          "Gaston Leroux", 1907),
    (6133,  "The Extraordinary Adventures of Arsene Lupin", "Maurice Leblanc", 1907),
    (57669, "The Thinking Machine",                    "Jacques Futrelle", 1907),
    (10556, "The Old Man in the Corner",               "Baroness Orczy", 1909),
    (558,   "The Thirty-Nine Steps",                   "John Buchan", 1915),
]


def download(book_id, dest):
    """Fetch one plain-text book. Skips files already on disk, so a re-run
    after a dropped connection only fetches what is missing."""
    if dest.exists() and dest.stat().st_size > 0:
        return "already there"
    request = urllib.request.Request(
        MIRROR_URL.format(id=book_id),
        headers={"User-Agent": "Mozilla/5.0 (book-corpus-builder)"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        dest.write_bytes(response.read())
    time.sleep(1)  # be polite to a volunteer-run mirror
    return "downloaded"


def main():
    config.BOOKS_DIR.mkdir(parents=True, exist_ok=True)

    catalog = []
    for book_id, title, author, year in BOOKS:
        dest = config.BOOKS_DIR / f"{title}.txt"
        status = download(book_id, dest)
        print(f"  {status:<14} {dest.name}  ({dest.stat().st_size / 1e6:.2f} MB)")
        catalog.append({
            "file": dest.name, "title": title, "author": author, "year": year,
            "gutenberg_id": book_id,
            "url": f"https://www.gutenberg.org/ebooks/{book_id}",
        })

    # The catalogue gives the web app an author and year for each file name,
    # without having to parse them back out of the Gutenberg header.
    with open(config.BOOK_CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    print(f"\n{len(catalog)} books in {config.BOOKS_DIR}")


if __name__ == "__main__":
    main()
