# PDR-001: Clauddy follows Claude only

- **Status**: Accepted
- **Date**: 2026-11-26
- **Supersedes**: [ADR-004](ADR-004-codex-and-cursor-are-opt-in.md), [ADR-011](ADR-011-codex-limits-from-the-app-server.md)
- **Related**: [design/04-usage.md](../design/04-usage.md), [design/02-features.md](../design/02-features.md)

## Context

Codex and Cursor were opt-in sources beside Claude: their own readers (`codex.rs`, `cursor.rs`), a Codex app-server, Cursor's unofficial dashboard endpoints read from the app's local storage, OpenAI's price list, tabs, alerts, reminders, remarks and a mood mixed across services. This fork is used with Claude Code alone; those paths were never exercised, cost a SQLite dependency and a third of the screen states, and every new feature had to decide what to do for three services.

## Decision

Clauddy tracks Claude only. Codex and Cursor are gone from the code: their readers, their settings (`codex` / `cursor` in `config.json` are ignored and no longer written), their screens and tabs, their alerts, reminders and remarks, OpenAI's prices and the `rusqlite` dependency. The mood comes from Claude alone. The `Provider` enum keeps its single `Claude` variant for now, so the branches built on it still merge; collapsing it is a later clean-up. The `service` theme keeps its key in `config.json` and reads as **Clay**.

## Alternatives considered

- **Hide them in the interface, keep the code**: a smaller change, but the code would still be built, tested and kept up with Codex's and Cursor's formats for nothing.
- **Keep them opt-in**: what ADR-004 did; nobody here turns them on.

## Consequences

- A saved Codex or Cursor reminder, or an alert armed for them, is dropped on the next read; nothing else in the user's data changes.
- Settings → Accounts shows the Claude card alone; the expanded panel never shows service tabs.
- Bringing another service back means new readers and a new record.
