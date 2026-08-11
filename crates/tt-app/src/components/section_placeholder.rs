//! Заглушка для разделов приложения

#![allow(clippy::incompatible_msrv)]

use crate::state::NavSection;
use dioxus::prelude::*;

/// Заглушка для разделов (пока экраны не реализованы)
#[allow(clippy::incompatible_msrv)]
#[component]
pub fn SectionPlaceholder(section: NavSection) -> Element {
    let title = match section {
        NavSection::Tasks => "Задачи",
        NavSection::Tracker => "Трекер активности",
        NavSection::Settings => "Настройки",
    };

    let description = match section {
        NavSection::Tasks => "Управление задачами, дедлайнами и приоритетами",
        NavSection::Tracker => "Отслеживание активности окон, бездействия и помодоро-таймер",
        NavSection::Settings => "Настройка приложения, аудио и параметров трекинга",
    };

    rsx! {
        div { class: "section-placeholder",
            div { class: "section-icon", "{get_section_icon(section)}" }
            h1 { class: "section-title", "{title}" }
            p { class: "section-description", "{description}" }
            p { class: "section-hint", "Раздел в разработке" }
        }
    }
}

fn get_section_icon(section: NavSection) -> &'static str {
    match section {
        NavSection::Tasks => "📋",
        NavSection::Tracker => "⏱️",
        NavSection::Settings => "⚙️",
    }
}
