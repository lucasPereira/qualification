---
name: import-bib-tex
description: >-
  Import a BibTeX reference into a .bib file with standardized keys,
  tab-indented formatting, year/title ordering, and matching updates in
  the paired .tex file. Use when the user pastes or provides a BibTeX entry,
  asks to add a reference, import bibliography, or normalize a .bib file.
disable-model-invocation: true
---

# Import BibTeX

Adds a BibTeX entry to a LaTeX project's `.bib` file, normalizes the whole bibliography to a fixed house standard, and keeps citation keys in the paired `.tex` file in sync. Use this when the user pastes a reference, asks to import bibliography, or wants an existing `.bib` normalized.

## Workflow

Resolve the target `.bib` and paired `.tex` first (see [Resolving target files](#resolving-target-files)). Run commands from the directory that contains the `.bib` file.

1. Read both files.
2. Run the import script with the user's raw `@type{...}` block:

```bash
python3 .cursor/skills/import-bib-tex/scripts/import-bibtex.py \
  --bib <bib> \
  --tex <tex> \
  --entry "$(cat <<'EOF'
@book{...,
  ...
}
EOF
)"
```

3. Read stdout for the new key, any renamed keys, and `.tex` updates.
4. Confirm the written files match [reference.md](reference.md).

Pass `--normalize-only` to reformat an existing `.bib` without adding an entry. If the script is unavailable, follow the manual checklist in [reference.md](reference.md).

## Resolving target files

The script needs explicit paths. When the user names them, use those paths. Otherwise, locate the main `.tex` (contains `\documentclass`) and the `.bib` it cites through `\bibliography{...}` or `\addbibresource{...}` without the extension. If more than one project matches, ask the user which pair to use. The script lives at `.cursor/skills/import-bib-tex/scripts/import-bibtex.py` relative to the project root. Path resolution examples: [examples.md](examples.md).

## House standard

Every import rewrites the entire `.bib`, not only the new entry. Entries use tab indentation, a fixed field order per type, and sort by year (newest first) then title. Citation keys follow `{surname}:{year}` for one author or `{surname}:etal:{year}` for two or more; distinct works that would share a key get suffixes `:a`, `:b`, `:c`, and so on. After any rename, update matching `\cite...{key}` commands in the paired `.tex`. Field order, templates, key algorithm, and citation patterns: [reference.md](reference.md). Worked cases: [examples.md](examples.md).

## Failure handling

**Invalid BibTeX.** Show the parse error and ask for a corrected entry.

**Duplicate work.** Report the existing key; do not add a second entry.

**Missing target files.** Ask for paths or inspect `\bibliography`/`\addbibresource` in the LaTeX sources.
