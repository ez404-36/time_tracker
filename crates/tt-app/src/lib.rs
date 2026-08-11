//! tt-app: приложение TimeTracker на Dioxus (библиотека)

pub mod components;
pub mod init;
pub mod services;
pub mod state;
pub mod theme;

pub use init::{get_db_path, init_logging};
pub use services::{AppServices, ServicesInitError};
pub use state::{theme_to_string, AppState, NavSection, Theme};
pub use theme::get_theme_css;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_theme_toggle() {
        let theme = Theme::Light;
        assert_eq!(theme.toggle(), Theme::Dark);
        assert_eq!(theme.toggle().toggle(), Theme::Light);
    }

    #[test]
    fn test_theme_as_str() {
        assert_eq!(Theme::Light.as_str(), "light");
        assert_eq!(Theme::Dark.as_str(), "dark");
    }

    #[test]
    fn test_nav_section_equality() {
        assert_eq!(NavSection::Tasks, NavSection::Tasks);
        assert_ne!(NavSection::Tasks, NavSection::Tracker);
    }

    #[test]
    fn test_nav_section_copy() {
        let section = NavSection::Settings;
        let copy = section;
        assert_eq!(section, copy);
    }
}
