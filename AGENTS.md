# Qualification document guidance

This file gives agents the context needed to edit, build, and review the doctorate qualification document at UFSC. The manuscript is a LaTeX project written in Brazilian Portuguese and formatted with the UFSC thesis template (`ufsc-thesis-rn46-2019`).

## Project scope

The project is a qualification manuscript, not an application codebase. The main entry point is `qualification.tex`. Formatting rules live in `template-guide.pdf`.

## Repository layout

These paths are the usual edit targets. Class files are template infrastructure; change them only when the build or the user requires it.

- `qualification.tex` — document root.
- `*.tex` chapters — body text included with `\input{}` from `qualification.tex`.
- `qualification.bib` — references cited from the manuscript.
- `ufsc-thesis-rn46-2019.cls`, `template-guide.pdf` — UFSC template.

**One chapter per file.** Add new chapters as separate `.tex` files and `\input{}` them from `qualification.tex`.

**Cite from the bibliography file.** Do not hardcode bibliography entries in chapter files.

**Leave the class alone.** Do not edit `ufsc-thesis-rn46-2019.cls` unless the user asks or the build requires it.

**Consult the template guide.** Before changing structure, margins, pre-textual elements, citations, or bibliography, read `template-guide.pdf`.

## Build

After substantive edits, compile when possible and check the PDF for unresolved references, missing citations, and serious overfull boxes.

```bash
latexmk -pdf qualification.tex
```

**Do not commit build artifacts.** Unless the user asks, omit `.aux`, `.bbl`, `.blg`, `.fdb_latexmk`, `.fls`, `.log`, and `.toc`.
