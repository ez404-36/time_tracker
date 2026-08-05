//! Реализация для Linux (X11 + Wayland)

// Оправдание: X11-реализация содержит RustConnection (~400 байт) и EwmhAtoms (~40 байт),
// что делает enum значительно больше Wayland-реализации. Boxing потребует дополнительных
// аллокаций при каждом вызове match в runtime, что негативно влияет на производительность.
// Так как типичное использование — это быстрые вызовы в горячем пути (idle_seconds),
// оправдано оставить enum без Box с этим allow.
#![allow(clippy::large_enum_variant)]
use crate::error::PlatformError;
use crate::WindowControl;
use std::env;

mod x11;

#[cfg(feature = "wayland")]
mod wayland;

/// Реализация WindowControl для Linux
pub enum LinuxWindowControl {
    /// X11 реализация
    X11(x11::X11WindowControl),
    /// Wayland реализация
    #[cfg(feature = "wayland")]
    Wayland(wayland::WaylandWindowControl),
}

impl LinuxWindowControl {
    /// Создаёт Linux-реализацию, автоматически выбирая X11 или Wayland
    pub fn new() -> Result<Self, PlatformError> {
        // Приоритет: X11 > Wayland
        if Self::is_x11_available() {
            tracing::info!("Используется X11 backend");
            Ok(LinuxWindowControl::X11(x11::X11WindowControl::new()?))
        } else if Self::is_wayland_available() {
            #[cfg(feature = "wayland")]
            {
                tracing::info!("Используется Wayland backend");
                Ok(LinuxWindowControl::Wayland(
                    wayland::WaylandWindowControl::new()?,
                ))
            }
            #[cfg(not(feature = "wayland"))]
            {
                Err(PlatformError::WaylandNotSupported(
                    "Wayland поддержка не скомпилирована. Добавьте feature 'wayland'.".to_string(),
                ))
            }
        } else {
            Err(PlatformError::Unsupported {
                platform: "Linux (ни X11, ни Wayland недоступен)".to_string(),
            })
        }
    }

    /// Проверяет доступность X11
    fn is_x11_available() -> bool {
        #[cfg(feature = "x11")]
        {
            env::var("DISPLAY").is_ok()
        }
        #[cfg(not(feature = "x11"))]
        {
            false
        }
    }

    /// Проверяет доступность Wayland
    fn is_wayland_available() -> bool {
        env::var("WAYLAND_DISPLAY").is_ok()
            || env::var("XDG_SESSION_TYPE").is_ok_and(|v| v == "wayland")
    }
}

impl WindowControl for LinuxWindowControl {
    fn active_window(&self) -> Result<Option<tt_core::WindowData>, PlatformError> {
        match self {
            LinuxWindowControl::X11(ctrl) => ctrl.active_window(),
            #[cfg(feature = "wayland")]
            LinuxWindowControl::Wayland(ctrl) => ctrl.active_window(),
        }
    }

    fn all_windows(&self) -> Result<Vec<tt_core::WindowData>, PlatformError> {
        match self {
            LinuxWindowControl::X11(ctrl) => ctrl.all_windows(),
            #[cfg(feature = "wayland")]
            LinuxWindowControl::Wayland(ctrl) => ctrl.all_windows(),
        }
    }

    fn idle_seconds(&self) -> Result<u64, PlatformError> {
        match self {
            LinuxWindowControl::X11(ctrl) => ctrl.idle_seconds(),
            #[cfg(feature = "wayland")]
            LinuxWindowControl::Wayland(ctrl) => ctrl.idle_seconds(),
        }
    }
}

/// Создаёт Linux-реализацию для Box<dyn WindowControl>
pub fn create_linux_window_control() -> Result<Box<dyn WindowControl>, PlatformError> {
    Ok(Box::new(LinuxWindowControl::new()?))
}
