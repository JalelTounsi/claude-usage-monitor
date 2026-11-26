# ADR-020: A theme repaints the panel, not the palette

- **Status**: Accepted
- **Date**: 2026-11-26
- **Related**: [design/02-features.md](../design/02-features.md#themes), [design/08-native.md](../design/08-native.md)

## Context

The panel had one look per service: clay brown for Claude, green-grey for Codex, steel blue for Cursor. People asked to pick another colour. Every colour is a `const` in `ui/theme.rs`, used about 220 times, and the text, bars and the pet's art were all tuned for a dark, warm panel.

## Decision

A theme (`theme` in `config.json`: `service`, `graphite`, `night`, `moss`, `plum`, `ink`) replaces only the panel's own colours: the card, its glow, the menus and the settings sheet (`Theme::panel` in `ui/theme.rs`). `service`, the default, is the original look, where each service tints the panel. Every theme is dark, so the text, the meters, the provider colours and the pet stay as they are. The theme reaches the screens through `Frame`, never through a global, so the snapshot gallery can render any of them side by side. An unknown name reads as `service`.

## Alternatives considered

- **Turning every token into a runtime value**: allows a light theme and free colour choice, but rewrites every use of `color::*` and puts each text colour's contrast in question for every panel.
- **A free colour picker**: any colour, but most of them break the contrast with the sand text and the coral accents.
- **A global theme read by the draw code**: fewer signatures to change, but the snapshot tests render in parallel and would fight over it.

## Consequences

- A new dark theme is four colours in `Theme::panel` and one snapshot case.
- A light theme still needs the whole palette to become per theme; it is a new record when it comes.
- The service tint no longer tells the tabs apart under a fixed theme; the tab plates and logos still do.
