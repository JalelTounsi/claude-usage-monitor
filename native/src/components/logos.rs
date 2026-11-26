// Provider logos, rasterized once
// at start-up into white masks and tinted when drawn.

use eframe::egui::{self, Color32, ColorImage, Rect, TextureHandle, TextureOptions};

use crate::ui::theme::color;

#[derive(Clone, Copy, PartialEq, Eq, Debug, Default, serde::Serialize, serde::Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Provider {
    #[default]
    Claude,
}

impl Provider {
    pub fn name(self) -> &'static str {
        match self {
            Provider::Claude => "Claude",
        }
    }
    /// The service's own usage page, which ⋯ → Usage page opens.
    pub fn usage_page(self) -> &'static str {
        match self {
            Provider::Claude => "https://claude.ai/settings/usage",
        }
    }
    /// The logo tint on a selected row and in the activity line.
    pub fn tint(self) -> Color32 {
        match self {
            Provider::Claude => color::CLAUDE,
        }
    }
    /// The panel's shade while it shows this service.
    pub fn surface(self) -> crate::ui::surface::Tint {
        use crate::ui::surface::Tint;
        match self {
            Provider::Claude => Tint::Claude,
        }
    }

    /// The usage bar.
    pub fn bar(self) -> Color32 {
        match self {
            Provider::Claude => color::CLAUDE_BAR,
        }
    }
    fn svg(self) -> &'static str {
        match self {
            Provider::Claude => include_str!("../../assets/logos/claude.svg"),
        }
    }
}

pub struct Logos {
    textures: Vec<(Provider, TextureHandle)>,
}

// rasterized large enough to stay crisp on a Retina screen at 12-14 px
const PX: u32 = 64;

impl Logos {
    pub fn load(ctx: &egui::Context) -> Self {
        let textures = [Provider::Claude]
            .into_iter()
            .map(|p| {
                let tree = resvg::usvg::Tree::from_str(p.svg(), &resvg::usvg::Options::default()).expect("embedded logo");
                let mut pm = resvg::tiny_skia::Pixmap::new(PX, PX).expect("logo pixmap");
                let k = PX as f32 / tree.size().width();
                resvg::render(&tree, resvg::tiny_skia::Transform::from_scale(k, k), &mut pm.as_mut());
                let img = ColorImage::from_rgba_premultiplied([PX as usize, PX as usize], pm.data());
                (p, ctx.load_texture(format!("logo-{}", p.name()), img, TextureOptions::LINEAR))
            })
            .collect();
        Logos { textures }
    }

    pub fn draw(&self, painter: &egui::Painter, p: Provider, rect: Rect, color: Color32) {
        if let Some((_, tex)) = self.textures.iter().find(|(q, _)| *q == p) {
            let uv = Rect::from_min_max(egui::pos2(0.0, 0.0), egui::pos2(1.0, 1.0));
            painter.image(tex.id(), rect, uv, color);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::Provider;

    #[test]
    fn claude_opens_its_usage_page() {
        assert!(Provider::Claude.usage_page().starts_with("https://claude.ai/"));
    }
}
