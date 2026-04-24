# Commander Cleanup Rules

- Commander rows are rebuilt from the validated battle snapshot, not patched from the old commander CSV.
- Commander extraction uses Wikipedia infobox commander cells as the source of truth.
- A second conservative recovery pass may upgrade or recover linked commanders only when the retained page itself contains a page-local linked-person match for the side-cell commander text.
- Linked commander candidates are accepted only if the cleaned name passes strict person-name rules and the linked page is not classified as a non-person page.
- Unlinked commander candidates are accepted only when the raw segment itself passes strict person-name rules.
- Nickname-only quoted fragments, graphic/template artifacts, narrative text, and non-person entities are excluded from the main commander file.
- Ambiguous or rejected commander candidates are moved to quarantine instead of remaining in the main commander file.
- `commanders_master.csv` is built only from validated commander rows.
