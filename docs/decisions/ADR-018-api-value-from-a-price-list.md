# ADR-018: The API value comes from a price list in the app

- **Status**: Accepted
- **Date**: 2026-11-24
- **Related**: [design/04-usage.md](../design/04-usage.md#api-value), [ADR-001](ADR-001-percent-from-the-account.md)

## Context

On a subscription the tokens have no bill, so nothing said what a week of Claude Code is worth. The local logs record, for every answer, its model and its tokens by kind (input, output, cache read, cache write and how long the write is kept), which is all the API bills on. The account reports no dollar figure, and prices change with each model.

## Decision

The dollar value of Claude's tokens is worked out in the app, from the local logs and a price list compiled into it (`native/src/pricing.rs`): each answer is priced once, when read, at its model's list price per kind of token. It is shown only when asked for (`apiValue`, off by default) and always as a value at API prices, never as a bill. A model missing from the list adds no dollars rather than a guessed price, and a new model gets its row in the list with its release.

## Alternatives considered

- **Fetching the prices at run time**: always current, but one more network call, a page to parse, and a number that changes with no release.
- **One average price per token**: one line of code, but cache reads cost a fortieth of output on some models, so the total would be off by a large factor.
- **The Usage and Cost API**: the real bill, but only for API organizations with an admin key; a subscription has none.

## Consequences

- The value works offline and on every plan, and the same logs always give the same total.
- The list goes stale when prices change: a release has to follow, and past tokens are then repriced at the new list.
- The Batch discount, fast mode's premium and Haiku 5.5's long-prompt price are not counted, so an API user's real bill can differ.
- Codex and Cursor stay in tokens.
