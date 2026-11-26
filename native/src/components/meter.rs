// The expanded panel's meters: label and % on top, a bar, a subtitle with
// the reset and the tokens behind it.

use eframe::egui::{Align2, Color32, FontId, Painter, Pos2, Rect, Vec2};
use std::time::Instant;

use crate::auth::Window;
use crate::format::{countdown, reset_in, tokens};
use crate::poller::Snapshot;
use crate::ui::bar::bar;
use crate::ui::skeleton::sk_line;
use crate::ui::text::bold;
use crate::ui::theme::{color, text};

pub const METER_H: f32 = 54.0;
// the session's meter leads with a big number
pub const HERO_H: f32 = 70.0;

/// The meter's height: the first one (the session) is the hero.
pub fn height(first: bool) -> f32 {
    if first { HERO_H } else { METER_H }
}

pub struct Meter {
    pub label: String,
    /// a quieter word after the label, smaller and dimmer ("up to 50%")
    pub note: Option<String>,
    pub pct: Option<f64>,
    pub sub: String,
}

/// A limits window still in force, its countdown rebased to now. A reading
/// whose reset already passed proves nothing about the new window: None,
/// never zero.
pub fn live(w: &Window, at: Option<Instant>) -> Option<(f64, Option<i64>)> {
    let elapsed = at.map(|a| a.elapsed().as_millis() as i64).unwrap_or(0);
    match w.reset_ms {
        Some(ms) if ms - elapsed <= 0 => None,
        Some(ms) => Some((w.pct, Some(ms - elapsed))),
        None => Some((w.pct, None)),
    }
}

/// One ramp for every meter: plain below 60, warm to 85, hot past it.
/// Returns (bar, number) colours.
pub fn level(pct: f64, accent: Color32) -> (Color32, Color32) {
    if pct >= 85.0 {
        (color::HOT, color::HOT)
    } else if pct >= 60.0 {
        (color::WARM, color::WARM)
    } else {
        (accent, color::FG)
    }
}

/// The session, the week, and any per-model weekly limits. Connected but not
/// read yet (or throttled): the meters stay, empty, rather than ask to log in.
/// `api_value`: the tokens read in dollars, at API prices.
pub fn meters(snap: &Snapshot, api_value: bool) -> Vec<Meter> {
    let (limits, at, usage) = (snap.limits.as_ref(), snap.limits_at, snap.usage.as_ref());
    let Some(l) = limits else {
        if !snap.connected {
            return vec![];
        }
        let sub = match snap.retry_at {
            Some(t) => format!("rate limited · retrying in {}", countdown(t.saturating_duration_since(Instant::now()).as_millis() as i64 + 59_999)),
            None => "waiting for a reading".into(),
        };
        let waiting = |label: &str| Meter { note: None, label: label.into(), pct: None, sub: sub.clone() };
        return vec![waiting("current session"), waiting("weekly · all models")];
    };
    let spent = |tk: u64, cost: f64| if api_value { crate::format::dollars(cost) } else { format!("{} tokens", tokens(tk)) };
    let session_spent = usage.map(|u| spent(u.session.tokens, u.session.cost)).unwrap_or_else(|| spent(0, 0.0));
    let week_spent = usage.map(|u| spent(u.week.tokens, u.week.cost)).unwrap_or_else(|| spent(0, 0.0));
    let session = live(&l.session, at);
    let week = live(&l.week, at);
    let weekly = |week: Option<(f64, Option<i64>)>| Meter {
        note: None,
        label: "weekly · all models".into(),
        pct: week.map(|w| w.0),
        sub: match week {
            Some((_, Some(ms))) => format!("resets in {} · {week_spent}", reset_in(ms)),
            _ => format!("{week_spent} · last 7 days"),
        },
    };
    // a weekly-only plan: the week leads, once
    let mut out = if l.weekly_only {
        vec![weekly(session)]
    } else {
        vec![
            Meter {
                note: None,
                label: "current session".into(),
                pct: session.map(|s| s.0),
                sub: match session {
                    Some((_, Some(ms))) => format!("resets in {} · {session_spent}", reset_in(ms)),
                    _ => "no active session".into(),
                },
            },
            weekly(week),
        ]
    };
    // per-model limits pair with that model family's local tokens
    for sc in &l.scoped {
        let Some((pct, reset)) = live(&Window { pct: sc.pct, reset_ms: sc.reset_ms }, at) else { continue };
        let key = sc.label.to_lowercase();
        let of_family = || usage.iter().flat_map(|u| &u.by_model).filter(|m| m.label.to_lowercase().starts_with(&key));
        let family = spent(of_family().map(|m| m.tokens).sum(), of_family().map(|m| m.cost).sum());
        out.push(Meter {
            // the most of the week it may take, when the plan says
            note: sc.share.map(|s| format!("up to {s:.0}% of the week")),
            label: format!("weekly · {key}"),
            pct: Some(pct),
            sub: match reset {
                Some(ms) => format!("resets in {} · {family}", reset_in(ms)),
                None => family,
            },
        });
    }
    out
}

/// Draw `m` between `left` and `right`, starting at `y`. The hero (the
/// session) has a 27 px number on the label's baseline and a thicker bar.
pub fn meter(p: &Painter, left: f32, right: f32, y: f32, m: &Meter, hero: bool, accent: Color32) {
    let (fill, num) = level(m.pct.unwrap_or(0.0), accent);
    let value = m.pct.map(|v| format!("{v:.0}%")).unwrap_or_else(|| "—".into());
    let (track_y, track_h) = if hero {
        let base = y + 8.0 + 30.0;
        p.text(Pos2::new(left, base), Align2::LEFT_BOTTOM, &m.label, FontId::proportional(text::BODY), color::FG_LABEL);
        p.text(Pos2::new(right, base + 4.0), Align2::RIGHT_BOTTOM, &value, FontId::proportional(text::HERO), num);
        (base + 9.0, 5.0)
    } else {
        let top = y + 19.0;
        let label = p.text(Pos2::new(left, top), Align2::LEFT_CENTER, &m.label, FontId::proportional(text::BODY), color::FG_LABEL);
        if let Some(note) = &m.note {
            p.text(Pos2::new(label.right() + 5.0, top + 0.5), Align2::LEFT_CENTER, note, FontId::proportional(text::SMALL), color::FG_SUB);
        }
        bold(p, Pos2::new(right, top), Align2::RIGHT_CENTER, &value, text::VALUE, num);
        (top + 14.0, 4.0)
    };
    let track = Rect::from_min_size(Pos2::new(left, track_y), Vec2::new(right - left, track_h));
    bar(p, track, m.pct.map(|v| (v / 100.0) as f32), fill, color::TRACK);
    p.text(Pos2::new(left, track.bottom() + 5.0), Align2::LEFT_TOP, &m.sub, FontId::proportional(text::SMALL), color::FG_SUB);
}

/// A meter's placeholder while the first reading loads.
pub fn meter_skeleton(p: &Painter, left: f32, right: f32, y: f32, hero: bool) {
    let (label_y, value_w, value_h, track_y, track_h) = if hero { (y + 30.0, 46.0, 20.0, y + 47.0, 5.0) } else { (y + 19.0, 26.0, 10.0, y + 33.0, 4.0) };
    sk_line(p, left, label_y, 86.0, 9.0);
    sk_line(p, right - value_w, label_y - (value_h - 9.0) / 2.0, value_w, value_h);
    bar(p, Rect::from_min_size(Pos2::new(left, track_y), Vec2::new(right - left, track_h)), None, color::TRACK, color::TRACK);
    sk_line(p, left, track_y + track_h + 11.0, 170.0, 8.0);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn an_expired_window_is_no_reading_not_zero() {
        assert_eq!(live(&Window { pct: 80.0, reset_ms: Some(-5) }, None), None);
        assert_eq!(live(&Window { pct: 80.0, reset_ms: Some(60_000) }, None).map(|r| r.0), Some(80.0));
    }

    #[test]
    fn the_ramp_is_plain_then_warm_then_hot() {
        assert_eq!(level(10.0, color::ACCENT), (color::ACCENT, color::FG));
        assert_eq!(level(60.0, color::ACCENT).0, color::WARM);
        assert_eq!(level(85.0, color::ACCENT).0, color::HOT);
    }

    #[test]
    fn no_account_means_no_meters() {
        assert!(meters(&Snapshot::default(), false).is_empty());
        let waiting = meters(&Snapshot { connected: true, ..Default::default() }, false);
        assert_eq!(waiting.len(), 2);
        assert!(waiting.iter().all(|m| m.pct.is_none()));
    }
}
