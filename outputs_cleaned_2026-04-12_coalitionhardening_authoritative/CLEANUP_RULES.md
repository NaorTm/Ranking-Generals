# Battle File Cleanup Rules

- The current frozen snapshot is preserved unchanged.
- Every original row is rebuilt from Wikipedia source evidence, preferring cached API data and using live API only when needed.
- Rows are kept in the main file only if they rebuild into an accepted `battle_article`, `war_conflict_article`, `campaign_article`, or `operation_article` with:
  - a valid date field set
  - a valid or conservative result field
  - enough event-specific source evidence to avoid weak-source classification
- Rows are removed completely if rebuild/classification indicates they are non-conflict pages, generic military concepts, biographies, organizations, missions, units, doctrines, manuals, or other false positives.
- Rows that still look like genuine conflict entries but cannot be validated confidently are moved to quarantine instead of staying in the main file.
- All kept rows are rewritten from the rebuilt source row rather than patched field by field.
- Result text is sanitized conservatively; malformed commentary-heavy result strings are reduced to a clean normalized label or `unknown`.
- Notes are standardized to `validated_rebuild_mode=<mode>` so the cleaned snapshot reflects actual rebuild provenance.
