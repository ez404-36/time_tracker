//! Верхняя панель приложения

#![allow(clippy::incompatible_msrv)]

use crate::state::Theme;
use dioxus::prelude::*;

/// Верхняя панель приложения
///
/// Содержит кнопку меню, переключатель темы и версию приложения.
#[allow(clippy::incompatible_msrv)]
#[component]
pub fn AppBar(theme: Signal<Theme>, version: String, on_menu_click: EventHandler<()>) -> Element {
    let theme_icon = if *theme.read() == Theme::Light {
        "🌙"
    } else {
        "☀️"
    };

    let theme_tooltip = if *theme.read() == Theme::Light {
        "Переключиться на тёмную тему"
    } else {
        "Переключиться на светлую тему"
    };

    rsx! {
        div { class: "app-bar",
            button {
                class: "app-bar-menu-button",
                onclick: move |_| on_menu_click(()),
                "☰"
            }
            div { class: "app-bar-title", "TimeTracker" }
            div { class: "app-bar-spacer" }
            div { class: "app-bar-version", "{version}" }
            button {
                class: "app-bar-theme-button",
                title: theme_tooltip,
                onclick: move |_| {
                    let current = *theme.read();
                    theme.set(current.toggle());
                },
                "{theme_icon}"
            }
        }
    }
}
