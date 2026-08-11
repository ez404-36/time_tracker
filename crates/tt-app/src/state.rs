//! Управление состоянием приложения

use dioxus::prelude::*;

/// Раздел навигации
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum NavSection {
    Tasks,
    Tracker,
    Settings,
}

/// Состояние приложения
///
/// Хранит только те данные, которые нужны для UI-рендеринга.
#[derive(Clone)]
pub struct AppState {
    pub theme: Signal<Theme>,
    pub current_section: Signal<NavSection>,
    pub sidebar_visible: Signal<bool>,
    pub snackbar_visible: Signal<bool>,
    pub snackbar_message: Signal<String>,
    pub modal_visible: Signal<bool>,
    pub modal_title: Signal<String>,
    pub modal_message: Signal<String>,
}

impl AppState {
    pub fn new(initial_theme: Theme) -> Self {
        Self {
            theme: Signal::new(initial_theme),
            current_section: Signal::new(NavSection::Tracker),
            sidebar_visible: Signal::new(true),
            snackbar_visible: Signal::new(false),
            snackbar_message: Signal::new(String::new()),
            modal_visible: Signal::new(false),
            modal_title: Signal::new(String::new()),
            modal_message: Signal::new(String::new()),
        }
    }
}

/// Тема приложения
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Theme {
    Light,
    Dark,
}

impl Theme {
    pub fn toggle(&self) -> Self {
        match self {
            Theme::Light => Theme::Dark,
            Theme::Dark => Theme::Light,
        }
    }

    pub fn as_str(&self) -> &str {
        match self {
            Theme::Light => "light",
            Theme::Dark => "dark",
        }
    }
}

/// Создаёт строковое представление темы для сохранения в БД
pub fn theme_to_string(theme: Theme) -> String {
    theme.as_str().to_string()
}
