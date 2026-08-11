//! Модальное окно

#![allow(clippy::incompatible_msrv)]

use dioxus::prelude::*;

/// Тип модального окна
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ModalType {
    /// Информационное сообщение
    Info,
    /// Ошибка
    Error,
}

impl ModalType {
    fn icon(&self) -> &'static str {
        match self {
            ModalType::Info => "ℹ️",
            ModalType::Error => "❌",
        }
    }
}

/// Модальное окно
#[allow(clippy::incompatible_msrv)]
#[component]
pub fn Modal(
    visible: Signal<bool>,
    modal_type: ModalType,
    title: String,
    message: String,
    on_confirm: EventHandler<MouseEvent>,
    on_cancel: EventHandler<MouseEvent>,
) -> Element {
    rsx! {
        if *visible.read() {
            div { class: "modal-overlay",
                div { class: "modal",
                    div { class: "modal-header",
                        div { class: "modal-icon", "{modal_type.icon()}" }
                        h3 { class: "modal-title", "{title}" }
                    }
                    div { class: "modal-body",
                        p { "{message}" }
                    }
                    div { class: "modal-footer",
                        button {
                            class: "modal-button modal-button-cancel",
                            onclick: on_cancel,
                            "Отмена"
                        }
                        button {
                            class: "modal-button modal-button-confirm",
                            onclick: on_confirm,
                            "OK"
                        }
                    }
                }
            }
        }
    }
}
