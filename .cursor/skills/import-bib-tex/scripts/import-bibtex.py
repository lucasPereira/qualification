#!/usr/bin/env python3
"""Import and normalize BibTeX entries into a .bib file; sync keys in .tex."""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

FIELD_ORDER: dict[str, list[str]] = {
    "article": [
        "title",
        "author",
        "year",
        "journal",
        "volume",
        "number",
        "pages",
        "doi",
        "url",
    ],
    "book": [
        "title",
        "author",
        "year",
        "edition",
        "publisher",
        "address",
        "isbn",
        "doi",
        "url",
    ],
    "inproceedings": [
        "title",
        "author",
        "year",
        "booktitle",
        "pages",
        "publisher",
        "address",
        "doi",
        "url",
    ],
    "incollection": [
        "title",
        "author",
        "year",
        "booktitle",
        "editor",
        "pages",
        "publisher",
        "address",
        "doi",
        "url",
    ],
    "phdthesis": ["title", "author", "year", "school", "address", "doi", "url"],
    "mastersthesis": ["title", "author", "year", "school", "address", "doi", "url"],
    "techreport": [
        "title",
        "author",
        "year",
        "institution",
        "number",
        "address",
        "doi",
        "url",
    ],
    "misc": ["title", "author", "year", "howpublished", "url", "note"],
    "online": ["title", "author", "year", "howpublished", "url", "note"],
}

DEFAULT_FIELD_ORDER = ["title", "author", "year"]

ENTRY_RE = re.compile(
    r"@(?P<type>\w+)\s*\{\s*(?P<key>[^,\s]+)\s*,(?P<body>.*?)^\}",
    re.MULTILINE | re.DOTALL | re.IGNORECASE,
)

FIELD_RE = re.compile(
    r"^\s*(?P<name>[a-zA-Z_]+)\s*=\s*(\{(?P<brace>[^}]*)\}|\"(?P<quote>[^\"]*)\")",
    re.MULTILINE,
)

CITE_RE = re.compile(r"(\\cite[a-zA-Z]*\{)([^}]+)(\})")


@dataclass
class BibEntry:
    entry_type: str
    key: str
    fields: dict[str, str] = field(default_factory=dict)

    @property
    def year(self) -> int:
        raw = self.fields.get("year", "").strip()
        match = re.search(r"\d{4}", raw)
        return int(match.group()) if match else 9999

    @property
    def title(self) -> str:
        return self.fields.get("title", "")

    def work_id(self) -> tuple[int, str]:
        return (self.year, normalize_text(self.title))


def ascii_fold(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def normalize_text(text: str) -> str:
    text = ascii_fold(text).lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def sort_title_key(title: str) -> str:
    return normalize_text(title)


def sort_entry_key(entry: BibEntry) -> tuple[int, int, str]:
    missing_year = entry.year == 9999
    year_rank = 0 if missing_year else -entry.year
    return (1 if missing_year else 0, year_rank, sort_title_key(entry.title))


def parse_authors(author_field: str) -> list[str]:
    if not author_field.strip():
        return []
    parts = re.split(r"\s+and\s+", author_field, flags=re.IGNORECASE)
    return [part.strip() for part in parts if part.strip()]


def author_surname(author: str) -> str:
    author = author.strip()
    if "," in author:
        surname = author.split(",", 1)[0].strip()
    else:
        surname = author.split()[-1]
    surname = ascii_fold(surname).lower()
    return re.sub(r"[^a-z0-9]", "", surname)


def base_key(entry: BibEntry) -> str:
    authors = parse_authors(entry.fields.get("author", ""))
    year = entry.year
    year_str = "nodate" if year == 9999 else str(year)

    if not authors:
        fallback = normalize_text(entry.title)[:20].replace(" ", "") or "unknown"
        return f"{fallback}:{year_str}"

    surname = author_surname(authors[0])
    if len(authors) > 1:
        return f"{surname}:etal:{year_str}"
    return f"{surname}:{year_str}"


def parse_entry_block(raw: str) -> BibEntry:
    match = ENTRY_RE.search(raw.strip())
    if not match:
        raise ValueError("Invalid BibTeX entry: could not parse @type{key, ...}")

    entry_type = match.group("type").lower()
    key = match.group("key").strip()
    body = match.group("body")
    fields: dict[str, str] = {}

    for field_match in FIELD_RE.finditer(body):
        name = field_match.group("name").lower()
        value = field_match.group("brace")
        if value is None:
            value = field_match.group("quote") or ""
        fields[name] = value.strip()

    return BibEntry(entry_type=entry_type, key=key, fields=fields)


def parse_bib_file(path: Path) -> list[BibEntry]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    return [parse_entry_block(match.group(0)) for match in ENTRY_RE.finditer(text)]


def dedupe_works(entries: list[BibEntry]) -> list[BibEntry]:
    seen: dict[tuple[int, str], BibEntry] = {}
    for entry in entries:
        seen[entry.work_id()] = entry
    return list(seen.values())


def assign_keys(entries: list[BibEntry]) -> dict[str, str]:
    """Return mapping old_key -> new_key for every entry whose key changed."""
    renames: dict[str, str] = {}
    groups: dict[str, list[BibEntry]] = {}

    for entry in entries:
        groups.setdefault(base_key(entry), []).append(entry)

    letters = "abcdefghijklmnopqrstuvwxyz"

    for base, group in groups.items():
        ordered = sorted(group, key=sort_entry_key)
        if len(ordered) == 1:
            entry = ordered[0]
            if entry.key != base:
                renames[entry.key] = base
                entry.key = base
            continue

        for index, entry in enumerate(ordered):
            new_key = f"{base}:{letters[index]}"
            if entry.key != new_key:
                renames[entry.key] = new_key
                entry.key = new_key

    return renames


def ordered_fields(entry: BibEntry) -> list[tuple[str, str]]:
    preferred = FIELD_ORDER.get(entry.entry_type, DEFAULT_FIELD_ORDER)
    seen: list[tuple[str, str]] = []
    used: set[str] = set()

    for name in preferred:
        if name in entry.fields:
            seen.append((name, entry.fields[name]))
            used.add(name)

    for name in sorted(entry.fields):
        if name not in used:
            seen.append((name, entry.fields[name]))
    return seen


def format_entry(entry: BibEntry) -> str:
    lines = [f"@{entry.entry_type}{{{entry.key},"]
    fields = ordered_fields(entry)
    for index, (name, value) in enumerate(fields):
        comma = "" if index == len(fields) - 1 else ","
        lines.append(f"\t{name}={{{value}}}{comma}")
    lines.append("}")
    return "\n".join(lines)


def sort_entries(entries: list[BibEntry]) -> list[BibEntry]:
    return sorted(entries, key=sort_entry_key)


def write_bib(path: Path, entries: list[BibEntry]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sorted_entries = sort_entries(entries)
    content = "\n\n".join(format_entry(entry) for entry in sorted_entries)
    path.write_text(content + "\n", encoding="utf-8")


def update_tex(path: Path, renames: dict[str, str]) -> list[str]:
    if not renames or not path.exists():
        return []

    text = path.read_text(encoding="utf-8")
    changes: list[str] = []

    def replace_cite(match: re.Match[str]) -> str:
        prefix, key, suffix = match.group(1), match.group(2), match.group(3)
        if key in renames:
            changes.append(f"{key} → {renames[key]}")
            return f"{prefix}{renames[key]}{suffix}"
        return match.group(0)

    updated = CITE_RE.sub(replace_cite, text)
    if updated != text:
        path.write_text(updated, encoding="utf-8")
    return changes


def import_entry(
    bib_path: Path,
    tex_path: Path | None,
    raw_entry: str | None,
    normalize_only: bool = False,
) -> None:
    existing = parse_bib_file(bib_path)
    new_key: str | None = None
    renames: dict[str, str] = {}
    entries = existing

    if raw_entry and not normalize_only:
        incoming = parse_entry_block(raw_entry)
        duplicate = next(
            (entry for entry in existing if entry.work_id() == incoming.work_id()),
            None,
        )
        if duplicate:
            print(f"Duplicate work; keeping existing key: {duplicate.key}")
            return

        existing.append(incoming)
        entries = dedupe_works(existing)
        renames = assign_keys(entries)
        new_key = incoming.key
    elif normalize_only:
        entries = dedupe_works(existing)
        renames = assign_keys(entries)
    else:
        raise ValueError("Provide --entry or use --normalize-only")

    write_bib(bib_path, entries)

    tex_changes: list[str] = []
    if tex_path:
        tex_changes = update_tex(tex_path, renames)

    print(f"Wrote {bib_path} ({len(entries)} entries)")
    if new_key:
        print(f"Entry key: {new_key}")
    if renames:
        print("Renamed keys:")
        for old, new in sorted(renames.items()):
            print(f"  {old} → {new}")
    if tex_path:
        if tex_changes:
            print(f"Updated {tex_path}:")
            for change in tex_changes:
                print(f"  \\cite...{{{change}}}")
        else:
            print(f"No citation updates needed in {tex_path}")
    elif renames:
        print("Warning: .tex not provided; citation keys were not synced.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Import/normalize BibTeX entries.")
    parser.add_argument("--bib", required=True, type=Path, help="Target .bib file")
    parser.add_argument("--tex", type=Path, help="Paired .tex file for cite sync")
    parser.add_argument("--entry", help="Raw BibTeX entry to import")
    parser.add_argument(
        "--normalize-only",
        action="store_true",
        help="Reformat and re-key existing entries without adding new one",
    )
    args = parser.parse_args()

    if not args.entry and not args.normalize_only:
        parser.error("Provide --entry or use --normalize-only")

    try:
        import_entry(args.bib, args.tex, args.entry, args.normalize_only)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
