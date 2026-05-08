# ReadMine Output Directory

This directory contains generated documentation produced by:

```text
CREW/Crew/ReadMine.py
```

## Current Output Shape

ReadMine currently generates **beginner-only** content for each subject:

```text
Reading Now/<Subject>/
Reading Now/<Subject>/index.html
Reading Now/<Subject>/beginner/theory.txt
Reading Now/<Subject>/beginner/usage.txt
Reading Now/<Subject>/beginner/examples.txt
Reading Now/<Subject>/beginner/*.meta.json
Reading Now/<Subject>/beginner/*_links.txt
```

Older `intermediate/` and `advanced/` folders are now pruned by the production ReadMine flow.

## Legacy Subject-Root Files

Some subject folders may still contain older files such as:

- `theory.txt`
- `usage.txt`
- `examples.txt`
- `links.txt`

These are legacy artifacts from earlier fetch-docs workflows and are not the main output shape of the current production ReadMine generator.

## Source of Truth

Use the production implementation in `CREW/Crew/ReadMine.py`.

Do not assume copies under `xCrew`, `xxCrew`, or `CREW/BACKUP` reflect the current live behavior.
