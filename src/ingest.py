"""
Step 1: Load the books and split them into overlapping text chunks.

CHUNKING STRATEGY (fixed-size, paragraph-aware, with overlap)
---------------------------------------------------------------
There are two common approaches:

  1. Fixed-size chunking: slice text into chunks of ~N characters/tokens,
     optionally overlapping consecutive chunks so an idea that falls on a
     boundary still appears whole in at least one chunk. Simple, fast,
     no extra model needed, and it's the standard baseline for RAG projects.

  2. Semantic chunking: use an embedding model (or an LLM) to detect topic
     shifts and cut at natural "meaning boundaries" instead of a fixed size.
     Produces more coherent chunks, but is slower, needs an extra model
     call per document, and is harder to reason about / explain simply.

For this project we use fixed-size chunking (~1000 characters, 200-char
overlap), but we don't slice blindly through the middle of a paragraph.
We split each chapter into paragraphs, then greedily pack whole paragraphs
into a chunk until adding the next one would exceed the size budget. This is
still "fixed-size chunking" (no embedding model involved) but it respects
natural text boundaries -- and a novel already has strong ones: chapters,
and paragraphs separated by blank lines.

WHAT IS DIFFERENT ABOUT BOOKS (vs. the research papers this started on)
-------------------------------------------------------------------------
This pipeline was first built over PDF research papers. Three things change
for plain-text books, and each is handled here:

  1. Citations point at a CHAPTER, not a page. Plain-text books have no
     pages -- page numbers would depend on whoever converted the file. A
     chapter ("The Hound of the Baskervilles, Chapter 6: Baskerville Hall")
     is how people actually refer to a place in a book, so each chunk
     carries one. Chunks never cross a chapter boundary, so the label is
     always exact.

  2. Project Gutenberg wraps every book in a licence header and footer.
     That text is identical across all 23 books, so if it were indexed, a
     question about "copyright" would match all of them equally. It is cut
     off at the standard "*** START/END OF THE PROJECT GUTENBERG EBOOK"
     markers before anything else happens.

  3. A passage from a novel rarely says which novel it is from. A paper
     repeats its method name on every page; a chapter of a Sherlock Holmes
     story just says "Holmes" and "Watson", like sixty other stories. So
     every chunk starts with a one-line label -- book and chapter -- which
     both the search and the model see. Without it, a question that names
     the story ("In The Speckled Band, ...") has nothing in the passage to
     match, and the model cannot tell which book a passage came from when a
     question compares two of them.

     Measured, not assumed: the same 13,430 chunks embedded with and without
     the label, scored on the 77 answerable test questions --
                          without label   with label
         right book 1st       0.65           0.78
         MRR                  0.74           0.84
         Hit Rate@5           0.88           0.92
     The intervals overlap a little, so the direction is clear and the exact
     size is not. The gain comes from questions that name a story; on the 12
     reworded questions that name nothing, the label slightly hurt (0.83 ->
     0.67, n=12) -- worth knowing, not worth undoing.
"""

import difflib
import json
import re

from tqdm import tqdm

import config

# --- 1. Reading a Gutenberg file ---------------------------------------------

GUTENBERG_START = re.compile(r"\*\*\*\s*START OF (THE|THIS) PROJECT GUTENBERG[^*]*\*\*\*", re.I)
GUTENBERG_END = re.compile(r"\*\*\*\s*END OF (THE|THIS) PROJECT GUTENBERG", re.I)


def read_book_text(path):
    """Return the body of one book: licence header and footer removed,
    line endings normalised, and _italics_ markers dropped."""
    text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    start = GUTENBERG_START.search(text)
    end = GUTENBERG_END.search(text)
    body = text[start.end() if start else 0: end.start() if end else len(text)]
    # Gutenberg marks italics as _word_. The underscores are formatting, not
    # text, and would otherwise leak into answers and break exact-match checks.
    return re.sub(r"_([^_\n]+)_", r"\1", body)


# --- 2. Finding chapters -----------------------------------------------------
#
# Every book formats its headings a little differently. Looking at all 23
# books, there are two families:
#
#   Novels: a pattern finds them.
#       CHAPTER I.  /  Chapter 6.  /  Chapter I       (title on the same or next line)
#       PART II.                                      (chapter numbers restart in each part)
#
#   Story collections: no pattern can. The heading is just the story's title,
#   in whatever style that edition uses --
#       I. A SCANDAL IN BOHEMIA
#       THE ADVENTURE OF THE EMPTY HOUSE
#       The Blue Cross
#       ONE -- The Absence of Mr Glass
#   -- and a rule loose enough to catch all of those also catches the letters,
#   telegrams and signs inside the stories ("BAKER STREET,", "DEAR MR. HOLMES").
#
# What every collection DOES have is a table of contents listing exactly those
# titles. So a line counts as a story heading only if it matches an entry in
# the book's own contents list. The book says what its chapters are; the code
# does not guess.
#
# A heading line must also start at the left margin, with a blank line above
# it. Gutenberg indents the contents list, so that rule stops the contents
# page itself from being read as a run of empty chapters.

NUMBER = r"(?:[IVXLCDM]+|\d+|[A-Z][A-Za-z]+)"   # roman, arabic, or a word ("One")
CHAPTER_RE = re.compile(rf"^(?:CHAPTER|Chapter|CHAP\.)\s+({NUMBER})\b\.?\s*[.:\-—]?\s*(.*)$")
PART_RE = re.compile(rf"^(?:PART|Part|BOOK|Book)\s+({NUMBER})\b\.?\s*[.:\-—]?\s*(.*)$")
CONTENTS_RE = re.compile(r"^(?:TABLE OF )?CONTENTS[.:]?$", re.I)
# A page number in a contents list sits after a wide gap: "FACTS AND
# DEDUCTIONS      17". The gap matters -- "The Problem of Cell 13" is a title.
PAGE_NUMBER_RE = re.compile(r"\s{2,}\d+$")

# The numbering in front of a title: "I.", "XII ", "1.", "ONE --", "Chapter 3 ".
# A Roman numeral only counts when followed by a dot, a dash or two spaces, so
# a title that merely starts with a word like "Civil" is left alone.
NUMBERING_RE = re.compile(
    r"^(?:(?:chapter|part|book)\s+)?"
    r"(?:[ivxlc]+|\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
    r"(?:\.\s*|\s*(?:--|—|:)\s*|\s{2,})",
    re.I,
)
FOOTNOTE_RE = re.compile(r"\(\*\d+\)")   # Poe's editions mark notes as "(*1)"

MAX_HEADING_CHARS = 90
SMALL_WORDS = {"a", "an", "and", "as", "at", "by", "for", "in", "of", "on",
               "or", "the", "to", "with", "from", "into"}


def tidy_title(title):
    """'THE ADVENTURE OF THE ENGINEER'S THUMB.' -> "The Adventure of the Engineer's Thumb".

    Gutenberg headings are often in capitals. str.title() would turn
    "ENGINEER'S" into "Engineer'S", so words are capitalised one at a time.
    Titles already in mixed case are left alone apart from trailing dots.
    """
    title = FOOTNOTE_RE.sub("", title).strip().rstrip(".").strip()
    if title != title.upper():
        return title
    words = title.lower().split()
    out = []
    for i, word in enumerate(words):
        if i > 0 and word in SMALL_WORDS:
            out.append(word)
        elif "." in word.rstrip("."):
            out.append(word.upper())          # initials and degrees: "M.D.", "J.B."
        else:
            # Capitalise the first LETTER, not the first character, so a title
            # that opens with a quotation mark still gets a capital.
            first = next((j for j, ch in enumerate(word) if ch.isalpha()), 0)
            out.append(word[:first] + word[first:first + 1].upper() + word[first + 1:])
    return " ".join(out)


def strip_numbering(title):
    """'I.     A Scandal in Bohemia' -> 'A Scandal in Bohemia'."""
    return NUMBERING_RE.sub("", title.strip(), count=1)


def title_key(title):
    """A comparison key that ignores case, quotes and punctuation, so the
    contents entry "The Stockbroker's Clerk" matches the heading
    "THE STOCKBROKER'S CLERK" whatever kind of apostrophe each one uses."""
    title = FOOTNOTE_RE.sub("", strip_numbering(title)).lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", title).split())


def find_contents(lines):
    """Read the table of contents: ({title_key: title as printed}, end_line).

    The list starts after a "Contents" line. Gutenberg indents the entries,
    so the list ends at the first line back at the left margin -- or, for an
    edition that does not indent, at a run of three blank lines. (Ending only
    on blank lines was the first version, and it ran straight on into The
    Moonstone, whose contents are followed by just two, turning 700 ordinary
    paragraphs into "chapters".)

    Bare numerals ("I", "II") are skipped: The Moonstone lists its unnamed
    sections that way, and every "I" in the text would otherwise become a
    heading. A title with a subtitle ("His Last Bow: The War Service of
    Sherlock Holmes") is also stored under its first half, because that is
    all the heading itself may say. Returns ({}, 0) if there is no list.
    """
    for i, line in enumerate(lines):
        if CONTENTS_RE.match(line.strip()):
            break
    else:
        return {}, 0

    titles, blank_run, indented = {}, 0, None
    previous = None          # (key, title, column the title text starts at)
    end = len(lines)
    for j in range(i + 1, len(lines)):
        line = lines[j]
        if not line.strip():
            blank_run += 1
            if blank_run >= 3 and titles:
                end = j
                break
            continue
        blank_run = 0
        if indented is None:
            indented = line != line.lstrip()     # decided by the first entry
        elif indented and line == line.lstrip():
            end = j                              # back at the margin: the text starts
            break

        stripped = line.strip()
        unnumbered = strip_numbering(stripped) == stripped
        indent = len(line) - len(line.lstrip())

        # A long title wraps onto a second, unnumbered line indented to where
        # the title above it starts (The Mystery of the Yellow Room). That line
        # finishes the previous entry; on its own it would become a bogus
        # "chapter" called "Everything".
        if previous and unnumbered and indent >= previous[2]:
            key, title, column = previous
            title = PAGE_NUMBER_RE.sub("", f"{title} {stripped}").strip().rstrip(".")
            titles[key] = title                      # the first line still finds it
            titles.setdefault(title_key(title), title)
            previous = (key, title, column)
            continue

        title = FOOTNOTE_RE.sub("", strip_numbering(stripped)).strip()
        title = PAGE_NUMBER_RE.sub("", title).strip().rstrip(".")
        key = title_key(title)
        if not key or key == "page" or re.fullmatch(r"[ivxlc]+|\d+", key):
            previous = None
            continue
        titles.setdefault(key, title)
        if ":" in title:
            short = title.split(":")[0].strip()
            titles.setdefault(title_key(short), short)
        column = indent + len(stripped) - len(strip_numbering(stripped))
        previous = (key, title, column) if not unnumbered else None
    return titles, end


def match_contents(lines, i, contents):
    """The contents title that line i is the heading for, or None.

    Exact match on the comparison key first. Failing that, a near match (90%
    similar) is accepted for a line standing alone between blank lines --
    editions are not always consistent with themselves: Poe's contents list
    "HANS PFAALL" while the heading in the text says "PFAAL".
    """
    key = title_key(lines[i])
    if not key:
        return None
    if key in contents:
        return contents[key]
    stands_alone = i + 1 >= len(lines) or not lines[i + 1].strip()
    if stands_alone and len(key) >= 10:
        close = difflib.get_close_matches(key, contents.keys(), n=1, cutoff=0.9)
        if close:
            return contents[close[0]]
    return None


def _at_margin(line):
    return bool(line.strip()) and line == line.lstrip() and len(line) <= MAX_HEADING_CHARS


def _is_heading_position(lines, i):
    """A heading sits at the left margin with a blank line above it."""
    return _at_margin(lines[i]) and (i == 0 or not lines[i - 1].strip())


def _next_line_title(lines, i, contents):
    """For a bare 'Chapter I', find its title below it: (title, lines used).

    Usually the title is on the very next line. Some editions leave a blank
    line first (The Mystery of the Yellow Room), and that case is only
    accepted when the line is in the contents list -- otherwise the first
    sentence of a chapter with no title would be taken for one.
    """
    if i + 1 < len(lines) and _at_margin(lines[i + 1]):
        return lines[i + 1].strip(), 1
    for j in range(i + 2, min(i + 4, len(lines))):
        if lines[j].strip():
            if _at_margin(lines[j]) and match_contents(lines, j, contents):
                return lines[j].strip(), j - i
            break
    return "", 0


def split_chapters(text, book=""):
    """Split a book's body into [(chapter_label, chapter_text), ...].

    Text before the first heading (title page, contents, preface) becomes a
    section labelled "Front matter". Sections with almost no prose are
    dropped later, which is what removes title pages and stray headings.

    `book` is the book's own title. Novels list it at the top of their
    contents, and it must not become a prefix on every chapter label.
    """
    lines = text.split("\n")
    contents, contents_end = find_contents(lines)
    sections = []
    label, start = "Front matter", 0
    story, part = "", ""      # the enclosing story / part, for nested labels

    def close(at):
        sections.append((label, "\n".join(lines[start:at])))

    def context():
        """'Story, Part II' -- whatever encloses the next heading."""
        outer = "" if title_key(story) == title_key(book) else story
        return ", ".join(x for x in (outer, part) if x)

    i = 0
    while i < len(lines):
        if not _is_heading_position(lines, i):
            i += 1
            continue
        line = lines[i].strip()
        used = 0

        part_match = PART_RE.match(line)
        chapter_match = CHAPTER_RE.match(line)
        # Only look for contents titles AFTER the contents list: a title page
        # above it repeats the book's name, which is not a story heading.
        story_title = match_contents(lines, i, contents) if i >= contents_end else None

        if part_match:
            # A part is context, not a chapter. In a novel it prefixes the
            # chapters ("Part II, Chapter I"). A bare "PART II" inside a
            # story is a section of that story ("The Adventure of the Red
            # Circle, Part II"); a titled one ("BOOK II. HENRY CLAVERING")
            # is a new top-level division, so it starts fresh.
            close(i)
            title = part_match.group(2)
            if not title:
                title, used = _next_line_title(lines, i, contents)
                if CHAPTER_RE.match(title):
                    title, used = "", 0       # the next line is a chapter, not a title
            if title:
                story = ""
            word = line.split()[0].capitalize()   # "Part" or "Book", as the book says
            part = f"{word} {part_match.group(1)}"
            label = context()
            if title:
                label += f": {tidy_title(title)}"
        elif chapter_match:
            close(i)
            number, title = chapter_match.group(1), chapter_match.group(2)
            if not title:
                title, used = _next_line_title(lines, i, contents)
            label = f"Chapter {number}" + (f": {tidy_title(title)}" if title else "")
            if context():
                label = f"{context()}, {label}"
        elif story_title:
            # A story collection's heading, confirmed by its contents list.
            # The contents version of the title is used, because it is
            # usually in normal case where the heading is in capitals.
            close(i)
            story = tidy_title(story_title)
            part = ""
            label = story
        else:
            i += 1
            continue

        start = i + 1 + used
        i = start

    close(len(lines))
    return sections


# --- 3. Paragraphs and chunks ------------------------------------------------

MIN_PARAGRAPH_CHARS = 20     # drops stray numerals, "THE END", lone headings
MIN_SECTION_CHARS = 400      # drops title pages and contents lists


def sections_to_paragraphs(sections):
    """Flatten [(label, text)] into [(label, paragraph)], splitting on blank lines.

    Gutenberg hard-wraps lines at ~70 characters, so the line breaks inside a
    paragraph are re-joined with spaces.
    """
    paragraphs = []
    for label, text in sections:
        paras = [" ".join(p.split()) for p in text.split("\n\n")]
        paras = [p for p in paras if len(p) >= MIN_PARAGRAPH_CHARS]
        if sum(len(p) for p in paras) < MIN_SECTION_CHARS:
            continue
        paragraphs.extend((label, p) for p in paras)
    return paragraphs


def chunk_paragraphs(paragraphs, chunk_size, overlap):
    """
    Greedily pack (chapter, paragraph) pairs into chunks of at most
    `chunk_size` characters, then prepend the tail of the previous chunk to
    each chunk to create `overlap` characters of shared context.

    A chunk never spans two chapters: a new chapter always starts a new
    chunk, and the overlap is only taken from the same chapter. That keeps
    every chunk's chapter label exactly right.

    Returns a list of dicts: {text, chapter}.
    """
    raw_chunks = []  # each item: {"text": str, "chapter": str}
    current_text, current_chapter = "", None

    def flush():
        if current_text:
            raw_chunks.append({"text": current_text, "chapter": current_chapter})

    for chapter, para in paragraphs:
        same_chapter = chapter == current_chapter
        if same_chapter and len(current_text) + len(para) + 2 <= chunk_size:
            current_text = f"{current_text}\n\n{para}" if current_text else para
            continue

        flush()
        current_chapter = chapter
        if len(para) > chunk_size:
            # Rare case: a single paragraph is bigger than the whole chunk
            # budget (a long letter or confession). Hard-split it by characters.
            step = chunk_size - overlap
            for i in range(0, len(para), step):
                raw_chunks.append({"text": para[i:i + chunk_size], "chapter": chapter})
            current_text = ""
        else:
            current_text = para
    flush()

    # Add overlap: prepend the tail of the previous chunk, within one chapter.
    overlapped = []
    for i, chunk in enumerate(raw_chunks):
        prev = raw_chunks[i - 1] if i else None
        if prev and prev["chapter"] == chunk["chapter"] and overlap:
            text = f"{prev['text'][-overlap:]}\n\n{chunk['text']}"
        else:
            text = chunk["text"]
        overlapped.append({"text": text, "chapter": chunk["chapter"]})
    return overlapped


def book_title(source_book):
    """'The Moonstone.txt' -> 'The Moonstone'."""
    return source_book[:-4] if source_book.lower().endswith(".txt") else source_book


def chunk_label(source_book, chapter):
    """The one-line label every chunk starts with. See point 3 in the docstring."""
    return f"{book_title(source_book)} — {chapter}"


def chunks_from_text(text, source_book, chunk_size=None, overlap=None):
    """Shared core: a book's body text -> list of chunk records.

    `chunk_size`/`overlap` default to the values in config.py. They are
    parameters rather than constants so sweep.py can re-chunk the corpus at
    several sizes in one process to find out which one is actually best --
    without that, "why 1000 characters?" has no answer but "it seemed fine".
    """
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = config.CHUNK_OVERLAP if overlap is None else overlap

    sections = split_chapters(text, book=book_title(source_book))
    paragraphs = sections_to_paragraphs(sections)
    chunks = chunk_paragraphs(paragraphs, chunk_size, overlap)

    stem = book_title(source_book)
    records = []
    for i, chunk in enumerate(chunks):
        records.append({
            "chunk_id": f"{stem}__{i}",
            "source_book": source_book,
            "chunk_index": i,
            "chapter": chunk["chapter"],
            "text": f"{chunk_label(source_book, chunk['chapter'])}\n\n{chunk['text']}",
        })
    return records


def chunk_body(chunk):
    """A chunk's text without its leading label -- for showing to a reader,
    who already sees the book and chapter next to it."""
    label = chunk_label(chunk["source_book"], chunk["chapter"])
    text = chunk["text"]
    return text[len(label):].lstrip("\n") if text.startswith(label) else text


def process_book(path):
    """Turn one book file on disk into a list of chunk dicts, ready to embed."""
    return chunks_from_text(read_book_text(path), path.name)


def book_paths():
    """Every book in the corpus, in a fixed order."""
    return sorted(config.BOOKS_DIR.glob("*.txt"))


def main():
    paths = book_paths()
    if not paths:
        print(f"No books found in {config.BOOKS_DIR}. Run download_books.py first.")
        return

    all_chunks = []
    for path in tqdm(paths, desc="Chunking books"):
        try:
            all_chunks.extend(process_book(path))
        except Exception as e:
            print(f"Failed to process {path.name}: {e}")

    config.CHUNKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(config.CHUNKS_PATH, "w", encoding="utf-8") as f:
        for record in all_chunks:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Wrote {len(all_chunks)} chunks from {len(paths)} books to {config.CHUNKS_PATH}")


if __name__ == "__main__":
    main()
