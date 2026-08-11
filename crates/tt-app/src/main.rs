//! tt-app: приложение TimeTracker на Dioxus

#![allow(clippy::incompatible_msrv)]

use dioxus::prelude::*;
use tt_app::{components::*, get_theme_css, init_logging, AppState, NavSection, Theme};

/// Уникальный идентификатор приложения для single-instance и lock-файла.
const APP_ID: &str = "com.timetracker.tt-app";

/// Версия приложения
const VERSION: &str = "0.1.0";

/// Запускает приложение
fn main() {
    init_logging();

    let instance = single_instance::SingleInstance::new(APP_ID)
        .expect("Не удалось инициализировать single-instance guard");
    if !instance.is_single() {
        eprintln!("Другой экземпляр уже запущен");
        std::process::exit(1);
    }
    std::mem::forget(instance);

    dioxus::LaunchBuilder::new()
        .with_cfg(
            dioxus::desktop::Config::new().with_window(
                dioxus::desktop::WindowBuilder::new()
                    .with_title("TimeTracker")
                    .with_inner_size(dioxus::desktop::LogicalSize::new(1000.0, 700.0)),
            ),
        )
        .launch(app);
}

/// Корневой компонент приложения
fn app() -> Element {
    let mut initialized = use_signal(|| false);
    let mut app_state = use_signal(|| None::<AppState>);

    use_effect(move || {
        if *initialized.read() {
            return;
        }

        spawn(async move {
            let initial_theme = Theme::Light;

            app_state.set(Some(AppState::new(initial_theme)));
            initialized.set(true);
        });
    });

    if !*initialized.read() {
        rsx! {
            div { class: "loading-screen",
                div { class: "loading-spinner" }
                p { "Загрузка..." }
            }
        }
    } else {
        rsx! {
            AppContent { app_state }
        }
    }
}

/// Основной контент приложения
#[allow(clippy::incompatible_msrv)]
#[component]
fn AppContent(app_state: Signal<Option<AppState>>) -> Element {
    let mut sidebar_visible = {
        let state = app_state.read();
        match state.as_ref() {
            Some(s) => s.sidebar_visible,
            None => return rsx! { div { "AppState не инициализирован" } },
        }
    };

    let theme = {
        let state = app_state.read();
        match state.as_ref() {
            Some(s) => s.theme,
            None => return rsx! { div { "AppState не инициализирован" } },
        }
    };

    let current_section = {
        let state = app_state.read();
        match state.as_ref() {
            Some(s) => s.current_section,
            None => return rsx! { div { "AppState не инициализирован" } },
        }
    };

    let snackbar_visible = {
        let state = app_state.read();
        match state.as_ref() {
            Some(s) => s.snackbar_visible,
            None => return rsx! { div { "AppState не инициализирован" } },
        }
    };

    let snackbar_message = {
        let state = app_state.read();
        match state.as_ref() {
            Some(s) => s.snackbar_message,
            None => return rsx! { div { "AppState не инициализирован" } },
        }
    };

    let on_menu_click = move |_| {
        let current = *sidebar_visible.read();
        sidebar_visible.set(!current);
    };

    rsx! {
        div {
            class: "app-container",
            "data-theme": "{theme.read().as_str()}",

            AppBar {
                theme,
                version: VERSION.to_string(),
                on_menu_click,
            }

            div { class: "app-layout",
                Sidebar {
                    current_section,
                    sidebar_visible,
                }

                main { class: "main-content",
                    SectionPlaceholder { section: *current_section.read() }
                }
            }

            Snackbar {
                visible: snackbar_visible,
                message: snackbar_message.read().clone(),
            }

            style { {get_theme_css(*theme.read())} }
        }
    }
}

/// Боковая панель навигации
#[allow(clippy::incompatible_msrv)]
#[component]
fn Sidebar(current_section: Signal<NavSection>, sidebar_visible: Signal<bool>) -> Element {
    let sidebar_class = if *sidebar_visible.read() {
        "sidebar visible"
    } else {
        "sidebar"
    };

    rsx! {
        aside { class: sidebar_class,
            nav { class: "sidebar-nav",
                button {
                    class: get_nav_class(NavSection::Tracker, current_section),
                    onclick: move |_| current_section.set(NavSection::Tracker),
                    "Трекер активности"
                }
                button {
                    class: get_nav_class(NavSection::Tasks, current_section),
                    onclick: move |_| current_section.set(NavSection::Tasks),
                    "Задачи"
                }
                button {
                    class: get_nav_class(NavSection::Settings, current_section),
                    onclick: move |_| current_section.set(NavSection::Settings),
                    "Настройки"
                }
            }
        }
    }
}

fn get_nav_class(section: NavSection, current_section: Signal<NavSection>) -> &'static str {
    if *current_section.read() == section {
        "nav-item active"
    } else {
        "nav-item"
    }
}
