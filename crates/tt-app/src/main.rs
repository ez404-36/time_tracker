//! tt-app — пробный бинарник этапа 0.
//!
//! Проверка рисков до написания приложения:
//! - R1: окно системного webview открывается (dioxus desktop).
//! - R8/R9: иконка системного трея создаётся в главном потоке, внутри
//!   gtk event-loop dioxus (через `dioxus::desktop::trayicon`), меню работает.
//! - R10: single-instance блокирует вторую копию.

use dioxus::prelude::*;
use tray_icon::menu::{Menu, MenuItem};
use tray_icon::Icon;

/// Уникальный идентификатор приложения для single-instance и lock-файла.
const APP_ID: &str = "com.timetracker.tt-app";

fn main() {
    // R10: single-instance guard — строго первое действие процесса.
    let instance = single_instance::SingleInstance::new(APP_ID)
        .expect("failed to initialize single-instance guard");
    if !instance.is_single() {
        eprintln!("Another instance is running");
        std::process::exit(1);
    }
    // Удерживаем lock до конца процесса.
    std::mem::forget(instance);

    // R1: запуск desktop-приложения на системном webview.
    dioxus::LaunchBuilder::new()
        .with_cfg(
            dioxus::desktop::Config::new().with_window(
                dioxus::desktop::WindowBuilder::new()
                    .with_title("TimeTracker — Rust PoC")
                    .with_inner_size(dioxus::desktop::LogicalSize::new(440.0, 280.0)),
            ),
        )
        .launch(app);
}

/// Корневой компонент: создаёт трей-иконку и окно.
fn app() -> Element {
    let window = dioxus::desktop::use_window();

    // R8/R9: иконка создаётся строго в главном потоке, внутри gtk-loop dioxus,
    // ровно один раз (use_hook).
    use_hook(|| {
        let menu = build_tray_menu();
        let icon = build_tray_icon();
        dioxus::desktop::trayicon::init_tray_icon(menu, Some(icon));
    });

    // Обработка кликов по меню трея.
    dioxus::desktop::use_tray_menu_event_handler(move |event| match event.id().0.as_str() {
        "show" => window.set_visible(true),
        "exit" => window.close(),
        _ => {}
    });

    rsx! {
        style { {CSS} }
        div { class: "container",
            h1 { "TimeTracker — Rust PoC" }
            p { class: "subtitle", "Этап 0: проверка выполнимости" }
            ul {
                li { "R1: окно системного webview открыто ✓" }
                li { "R8: иконка в системном трее ✓" }
                li { "R10: single-instance блокирует вторую копию ✓" }
            }
            p { class: "hint", "Кликни правой по иконке в трее: «Показать окно» / «Выход»." }
        }
    }
}

/// Меню трея: «Показать окно» и «Выход».
fn build_tray_menu() -> Menu {
    let menu = Menu::new();
    let show = MenuItem::with_id("show", "Показать окно", true, None);
    let exit = MenuItem::with_id("exit", "Выход", true, None);
    menu.append_items(&[&show, &exit])
        .expect("failed to build tray menu");
    menu
}

/// Простая иконка 32×32 (сплошной синий RGBA), сгенерированная программно.
fn build_tray_icon() -> Icon {
    const SIZE: u32 = 32;
    let mut rgba = Vec::with_capacity((SIZE * SIZE * 4) as usize);
    for _ in 0..(SIZE * SIZE) {
        rgba.extend_from_slice(&[40, 96, 200, 255]);
    }
    Icon::from_rgba(rgba, SIZE, SIZE).expect("invalid tray icon rgba buffer")
}

const CSS: &str = r#"
body { font-family: system-ui, -apple-system, "Segoe UI", sans-serif; margin: 0; color: #1a1a1a; }
.container { padding: 24px; }
h1 { font-size: 20px; margin: 0 0 6px; }
.subtitle { margin: 0 0 14px; color: #555; }
ul { line-height: 1.7; margin: 0 0 14px; padding-left: 20px; }
.hint { font-size: 13px; color: #777; }
"#;
