//! tt-app: приложение TimeTracker на Dioxus

use dioxus::prelude::*;
use tracing::info;
use tracing_subscriber::{fmt, prelude::*, EnvFilter};

/// Уникальный идентификатор приложения для single-instance и lock-файла.
const APP_ID: &str = "com.timetracker.tt-app";

/// Путь к базе данных (будет использован при полной интеграции)
#[allow(dead_code)]
fn get_db_path() -> String {
    let mut path = std::env::current_dir().unwrap();
    path.push("timetracker.db");
    path.to_str().unwrap().to_string()
}

/// Инициализирует логирование с ретенцией 7 дней
fn init_logging() {
    let log_dir = std::env::current_dir().unwrap().join("logs");

    std::fs::create_dir_all(&log_dir).ok();

    let file_appender = tracing_appender::rolling::daily(&log_dir, "timetracker.log");
    let (non_blocking, _guard) = tracing_appender::non_blocking(file_appender);

    let env_filter = EnvFilter::from_default_env().add_directive(tracing::Level::INFO.into());

    tracing_subscriber::registry()
        .with(env_filter)
        .with(fmt::layer().with_writer(non_blocking))
        .with(fmt::layer().with_writer(std::io::stdout))
        .init();
}

/// Запускает приложение
fn main() {
    init_logging();
    info!("Запуск TimeTracker");

    // Single-instance guard
    let instance = single_instance::SingleInstance::new(APP_ID)
        .expect("failed to initialize single-instance guard");
    if !instance.is_single() {
        eprintln!("Another instance is running");
        std::process::exit(1);
    }
    std::mem::forget(instance);

    // Dioxus desktop имеет свой async runtime, но для совместимости
    // с async сервисами трекера мы используем отдельный tokio runtime
    // и связываем их через каналы.

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
    // Состояние загрузки
    let mut initialized = use_signal(|| false);
    let mut current_section = use_signal(|| NavSection::Tasks);

    // Инициализируем приложение один раз при монтировании компонента
    use_effect(move || {
        if *initialized.read() {
            return;
        }

        // Запускаем асинхронную инициализацию
        spawn(async move {
            // Инициализация сервиса трекера будет здесь
            // Для фазы 7.1 (фундамент без экранов) достаточно заглушки
            tracing::info!("Инициализация приложения (фаза 7.1 - фундамент UI)");
            initialized.set(true);
        });
    });

    rsx! {
        div { class: "app-container",
            // Боковая панель навигации
            aside { class: "sidebar",
                div { class: "sidebar-header", "TimeTracker" }
                nav { class: "sidebar-nav",
                    button {
                        class: if *current_section.read() == NavSection::Tasks {
                            "nav-item active"
                        } else {
                            "nav-item"
                        },
                        onclick: move |_| current_section.set(NavSection::Tasks),
                        "Задачи"
                    }
                    button {
                        class: if *current_section.read() == NavSection::Tracker {
                            "nav-item active"
                        } else {
                            "nav-item"
                        },
                        onclick: move |_| current_section.set(NavSection::Tracker),
                        "Трекер"
                    }
                    button {
                        class: if *current_section.read() == NavSection::Statistics {
                            "nav-item active"
                        } else {
                            "nav-item"
                        },
                        onclick: move |_| current_section.set(NavSection::Statistics),
                        "Статистика"
                    }
                    button {
                        class: if *current_section.read() == NavSection::Settings {
                            "nav-item active"
                        } else {
                            "nav-item"
                        },
                        onclick: move |_| current_section.set(NavSection::Settings),
                        "Настройки"
                    }
                }
            }

            // Основной контент
            main { class: "main-content",
                SectionPlaceholder { section: *current_section.read() }
            }
        }
        style { {CSS} }
    }
}

/// Заглушка для разделов (пока экраны не реализованы)
#[component]
fn SectionPlaceholder(section: NavSection) -> Element {
    let title = match section {
        NavSection::Tasks => "Задачи",
        NavSection::Tracker => "Трекер",
        NavSection::Statistics => "Статистика",
        NavSection::Settings => "Настройки",
    };

    rsx! {
        div { class: "section-placeholder",
            h1 { class: "section-title", "{title}" }
            p { class: "section-hint", "Раздел в разработке" }
        }
    }
}

/// Раздел навигации
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum NavSection {
    Tasks,
    Tracker,
    Statistics,
    Settings,
}

const CSS: &str = r#"
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
    font-size: 14px;
    color: #1a1a1a;
    background-color: #ffffff;
    line-height: 1.5;
}

.app-container {
    display: flex;
    height: 100vh;
    overflow: hidden;
}

.sidebar {
    width: 200px;
    background-color: #f5f5f5;
    display: flex;
    flex-direction: column;
    border-right: 1px solid #e0e0e0;
}

.sidebar-header {
    padding: 24px 16px;
    font-size: 24px;
    font-weight: 700;
    color: #1a1a1a;
    border-bottom: 1px solid #e0e0e0;
}

.sidebar-nav {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 8px;
}

.nav-item {
    padding: 12px 16px;
    border: none;
    background: none;
    text-align: left;
    font-size: 14px;
    font-weight: 400;
    color: #1a1a1a;
    cursor: pointer;
    border-radius: 6px;
    transition: background-color 0.2s;
}

.nav-item:hover {
    background-color: #e0e0e0;
}

.nav-item.active {
    background-color: #2c64c8;
    color: #ffffff;
    font-weight: 700;
}

.main-content {
    flex: 1;
    padding: 24px;
    overflow-y: auto;
    background-color: #ffffff;
}

.section-placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    gap: 16px;
}

.section-title {
    font-size: 36px;
    font-weight: 700;
    color: #1a1a1a;
}

.section-hint {
    font-size: 14px;
    color: #666666;
}
"#;
