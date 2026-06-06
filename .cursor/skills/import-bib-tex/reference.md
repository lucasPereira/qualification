# Import BibTeX Reference

Formatting rules, key generation, and the manual fallback. Workflow and triggers: [SKILL.md](SKILL.md). Worked cases: [examples.md](examples.md).

## Citation keys

**Base key.** One author: `{surname}:{year}` (e.g. `meszaros:2007`). Two or more: `{firstAuthorSurname}:etal:{year}` (e.g. `greiler:etal:2013`).

**Surname normalization.** Take the first author, split on `and`. Family name is the text before the first comma, or the last token otherwise. Lowercase ASCII: strip accents, remove spaces and punctuation (`van Deursen` → `vandeursen`).

**Collision suffix.** When the base key already identifies a different work (compare normalized `title` + `year`), rename every colliding entry with suffixes `:a`, `:b`, `:c`, … Example: two distinct works both map to `smith:2020` → `smith:2020:a`, `smith:2020:b`.

**Same work.** When `title` and `year` match an existing entry, keep the existing key; do not duplicate.

## Field order by entry type

Emit only fields present on the entry. Unknown fields go last, sorted alphabetically by field name.

| Type | Field order |
| --- | --- |
| `@article` | `title`, `author`, `year`, `journal`, `volume`, `number`, `pages`, `doi`, `url` |
| `@book` | `title`, `author`, `year`, `edition`, `publisher`, `address`, `isbn`, `doi`, `url` |
| `@inproceedings` | `title`, `author`, `year`, `booktitle`, `pages`, `publisher`, `address`, `doi`, `url` |
| `@incollection` | `title`, `author`, `year`, `booktitle`, `editor`, `pages`, `publisher`, `address`, `doi`, `url` |
| `@phdthesis`, `@mastersthesis` | `title`, `author`, `year`, `school`, `address`, `doi`, `url` |
| `@techreport` | `title`, `author`, `year`, `institution`, `number`, `address`, `doi`, `url` |
| `@misc`, `@online` | `title`, `author`, `year`, `howpublished`, `url`, `note` |
| default | `title`, `author`, `year`, then remaining fields alphabetically |

## Entry template

```bibtex
@book{meszaros:2007,
	title={xUnit test patterns: Refactoring test code},
	author={Meszaros, Gerard},
	year={2007},
	publisher={Pearson Education}
}
```

**Opening line.** `@type{key,` then newline.

**Fields.** One leading tab per line, `name={value}`, no spaces before braces. Last field has no trailing comma. Close with `}` on its own line.

**File layout.** One blank line between entries; no trailing blank line at end of file.

## Sorting

1. `year` descending, most recent first (missing year sorts last, treated as `9999`).
2. `title` ascending, case-insensitive.

## Key generation algorithm

```
authors ← parse author field (split on " and ")
surname ← family name of authors[0], normalized
base ← surname + ":etal:" + year  (if len(authors) > 1)
     ← surname + ":" + year        (otherwise)

if no entry with key base:
  return base

if entry with key base is same work (same normalized title and year):
  return existing key (no duplicate)

else:
  collect all entries whose key matches base or base + ":letter" [a-z]
  assign suffixes :a, :b, :c, ... by year then title
  rename existing entries; return next free suffix for the new entry
```

## Normalized title comparison

Lowercase, strip accents, remove punctuation, collapse whitespace. Used to detect same work vs collision.

## `.tex` citation patterns

After any key rename, replace the old key inside matching citation commands in the paired `.tex`. Do not change keys that were not renamed.

```regex
\\cite[a-zA-Z]*\{key\}
```

Matches `\cite{key}`, `\citeonline{key}`, `natbib` variants such as `\citep` and `\citet`, and any other `\cite...{key}` command.

## Manual normalize checklist

- [ ] Parse incoming entry; reject if `@type` or required fields missing.
- [ ] Load all existing entries from the target `.bib`.
- [ ] Assign key per [Citation keys](#citation-keys); resolve collisions with `:a`, `:b`, `:c`.
- [ ] Merge or skip if same work already present.
- [ ] Reformat every entry (tabs, field order).
- [ ] Sort by year (newest first), then title.
- [ ] Write the target `.bib`.
- [ ] Apply key renames to the paired `.tex`.
