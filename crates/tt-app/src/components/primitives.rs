//! Примитивы UI: Snackbar

#![allow(clippy::incompatible_msrv)]

use dioxus::prelude::*;

/// Snackbar для уведомлений
///
/// Отображается в нижнем правом углу экрана.
#[allow(clippy::incompatible_msrv)]
#[component]
pub fn Snackbar(visible: Signal<bool>, message: String) -> Element {
    rsx! {
        if *visible.read() {
            div { class: "snackbar",
                span { "{message}" }
            }
        }
    }
}
