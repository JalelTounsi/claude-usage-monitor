# ADR-019: The price list ships in the app and a file can correct it

- **Status**: Accepted
- **Date**: 2026-11-24
- **Related**: [design/04-usage.md](../design/04-usage.md#api-value), supersedes [ADR-018](ADR-018-api-value-from-a-price-list.md)

## Context

ADR-018 put the API value on a price list compiled into the app, for Claude only. Three things followed from it: a price change or a new model needed a release before the dollars were right again, a model missing from the list dropped out of the total without a word, and Codex stayed in tokens beside a Claude tab in dollars.

## Decision

The dollar value is still worked out in the app from the local logs, each answer priced once at its model's list price per kind of token, and shown only when asked for (`apiValue`). The list now has three layers, first match wins: `~/.claude-usage-monitor/prices.json` (read once at launch, names matched as a part of the model id, longest first), then OpenAI's prices for Codex (exact model id only), then Anthropic's for Claude. A model in none of them adds no dollars, and the panel says how many tokens have no price. The plan's price, used only to compare, is the one set in Settings or a plan with a single price; it is never guessed.

## Alternatives considered

- **Fetching the prices at run time**: always current, but a network call, a page to parse, and a number that changes with no release or edit behind it.
- **Pricing an unknown model as its nearest name**: fewer gaps, but a wrong price looks as sure as a right one; a stated gap is better.
- **Leaving Codex in tokens**: nothing to maintain, but the dollar mode then means something different on each tab.

## Consequences

- A stale or missing price is fixed by editing a file, with no release; the built-in list still gets its row with each new model.
- The file is trusted as written: a wrong price in it gives wrong dollars, and it takes a restart to be read.
- OpenAI's list is a second one to keep current, and its exact-id match leaves a model unpriced until it is listed.
- The Batch discount, fast mode's premium and long-prompt prices are still not counted.
