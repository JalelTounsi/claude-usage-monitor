// What a turn would have cost on the API: Anthropic's list prices per model,
// in USD per million tokens. A subscription pays none of this; it is the
// value of the tokens, not a bill.

/// One model's list prices, USD per million tokens.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Rates {
    pub input: f64,
    pub output: f64,
    pub cache_read: f64,
}

// a cache write costs the input price times this, by how long it is kept
const WRITE_5M: f64 = 1.25;
const WRITE_1H: f64 = 2.0;

// First match wins, so a newer id comes before the one it starts with
// (`opus-5-5` before `opus-5`). Legacy ids put the version first
// (`claude-3-5-haiku`), and fall to their family's last row.
const TABLE: [(&str, Rates); 21] = [
    ("fable-5-2", Rates { input: 8.0, output: 40.0, cache_read: 0.20 }),
    ("mythos-5-2", Rates { input: 8.0, output: 40.0, cache_read: 0.20 }),
    ("fable-5-1", Rates { input: 10.0, output: 50.0, cache_read: 0.25 }),
    ("mythos-5-1", Rates { input: 10.0, output: 50.0, cache_read: 0.25 }),
    ("fable", Rates { input: 10.0, output: 50.0, cache_read: 1.0 }),
    ("mythos", Rates { input: 10.0, output: 50.0, cache_read: 1.0 }),
    ("opus-5-5", Rates { input: 4.0, output: 20.0, cache_read: 0.20 }),
    ("opus-5", Rates { input: 5.0, output: 25.0, cache_read: 0.50 }),
    ("opus-4-8", Rates { input: 5.0, output: 25.0, cache_read: 0.50 }),
    ("opus-4-7", Rates { input: 5.0, output: 25.0, cache_read: 0.50 }),
    ("opus-4-6", Rates { input: 5.0, output: 25.0, cache_read: 0.50 }),
    ("opus-4-5", Rates { input: 5.0, output: 25.0, cache_read: 0.50 }),
    ("opus", Rates { input: 15.0, output: 75.0, cache_read: 1.50 }),
    ("sonnet-5-5", Rates { input: 2.0, output: 10.0, cache_read: 0.10 }),
    ("sonnet-5", Rates { input: 2.0, output: 10.0, cache_read: 0.20 }),
    ("sonnet", Rates { input: 3.0, output: 15.0, cache_read: 0.30 }),
    ("haiku-5-5", Rates { input: 0.10, output: 0.50, cache_read: 0.01 }),
    ("haiku-4-5", Rates { input: 1.0, output: 5.0, cache_read: 0.10 }),
    ("3-5-haiku", Rates { input: 0.80, output: 4.0, cache_read: 0.08 }),
    ("haiku-3-5", Rates { input: 0.80, output: 4.0, cache_read: 0.08 }),
    ("haiku", Rates { input: 0.25, output: 1.25, cache_read: 0.03 }),
];

/// The list prices for a model id, or None for one that isn't Claude's: an
/// unknown model is left out of the total rather than priced by a guess.
pub fn rates(model: &str) -> Option<Rates> {
    let m = model.to_lowercase();
    TABLE.iter().find(|(key, _)| m.contains(key)).map(|(_, r)| *r)
}

/// The tokens of one answer, by how the API bills them.
#[derive(Clone, Copy, Debug, Default, PartialEq)]
pub struct Tokens {
    pub input: u64,
    pub output: u64,
    pub cache_read: u64,
    /// cache writes kept 5 minutes (the default) and kept an hour
    pub write_5m: u64,
    pub write_1h: u64,
}

/// What these tokens cost on the API, in USD; 0 for an unknown model.
pub fn cost(model: Option<&str>, t: &Tokens) -> f64 {
    let Some(r) = model.and_then(rates) else { return 0.0 };
    let input = t.input as f64 + t.write_5m as f64 * WRITE_5M + t.write_1h as f64 * WRITE_1H;
    (input * r.input + t.output as f64 * r.output + t.cache_read as f64 * r.cache_read) / 1e6
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn a_newer_model_is_not_priced_as_the_one_its_id_starts_with() {
        assert_eq!(rates("claude-opus-5-5").map(|r| r.input), Some(4.0));
        assert_eq!(rates("claude-opus-5").map(|r| r.input), Some(5.0));
        assert_eq!(rates("claude-opus-4-1-20250805").map(|r| r.input), Some(15.0));
        assert_eq!(rates("claude-opus-4-5-20251101").map(|r| r.input), Some(5.0));
        assert_eq!(rates("claude-sonnet-5-5").map(|r| r.cache_read), Some(0.10));
        assert_eq!(rates("claude-sonnet-4-5-20250929").map(|r| r.input), Some(3.0));
        assert_eq!(rates("claude-fable-5-2").map(|r| r.output), Some(40.0));
        assert_eq!(rates("claude-haiku-4-5-20251001").map(|r| r.input), Some(1.0));
        assert_eq!(rates("claude-3-5-haiku-20241022").map(|r| r.input), Some(0.80));
        assert_eq!(rates("gpt-5"), None);
    }

    #[test]
    fn each_kind_of_token_is_billed_at_its_own_price() {
        let m = Some("claude-opus-5-5");
        let million = 1_000_000;
        assert_eq!(cost(m, &Tokens { input: million, ..Default::default() }), 4.0);
        assert_eq!(cost(m, &Tokens { output: million, ..Default::default() }), 20.0);
        assert_eq!(cost(m, &Tokens { cache_read: million, ..Default::default() }), 0.20);
        assert_eq!(cost(m, &Tokens { write_5m: million, ..Default::default() }), 5.0);
        assert_eq!(cost(m, &Tokens { write_1h: million, ..Default::default() }), 8.0);
        assert_eq!(cost(Some("gpt-5"), &Tokens { input: million, ..Default::default() }), 0.0);
        assert_eq!(cost(None, &Tokens { input: million, ..Default::default() }), 0.0);
    }
}
