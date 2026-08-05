//! Ошибки платформенного слоя

use thiserror::Error;

/// Ошибки платформенного слоя tt-platform
#[derive(Debug, Error)]
pub enum PlatformError {
    /// Платформа не поддерживается
    #[error("Платформа '{platform}' не поддерживается")]
    Unsupported { platform: String },

    /// Ошибка X11
    #[cfg(all(target_os = "linux", feature = "x11"))]
    #[error("Ошибка X11: {0}")]
    X11(#[from] x11rb::errors::ConnectionError),

    /// X11 недоступен (DISPLAY не установлен)
    #[cfg(all(target_os = "linux", feature = "x11"))]
    #[error("X11 недоступен: переменная окружения DISPLAY не установлена")]
    X11NotAvailable,

    /// Ошибка X11 при получении свойства окна
    #[cfg(all(target_os = "linux", feature = "x11"))]
    #[error("Ошибка X11 при получении свойства окна: {property}")]
    X11PropertyError { property: String },

    /// Wayland не поддерживается на текущей системе
    #[cfg(target_os = "linux")]
    #[cfg(feature = "wayland")]
    #[error("Wayland не поддерживается: {0}")]
    WaylandNotSupported(String),

    /// Для Wayland требуется включить unsafe_mode (только GNOME)
    #[cfg(target_os = "linux")]
    #[cfg(feature = "wayland")]
    #[error(
        "Для получения информации об окнах в Wayland требуется:\n\
         1. Окружение рабочего стола GNOME\n\
         2. Включённый unsafe_mode в настройках\n\
         Это ограничение безопасности Wayland. В X11 таких ограничений нет."
    )]
    WaylandUnsafeModeRequired,

    /// Ошибка D-Bus (для Wayland)
    #[cfg(target_os = "linux")]
    #[cfg(feature = "wayland")]
    #[error("Ошибка D-Bus: {0}")]
    DBus(#[from] zbus::Error),

    /// Ошибка Windows API
    #[cfg(windows)]
    #[error("Ошибка Windows API: {0}")]
    WindowsApi(String),

    /// Процесс не найден
    #[cfg(windows)]
    #[error("Процесс не найден: PID {0}")]
    ProcessNotFound(u32),

    /// Доступ запрещён
    #[cfg(windows)]
    #[error("Доступ запрещён к процессу: PID {0}")]
    AccessDenied(u32),

    /// Ошибка Windows (общая)
    #[cfg(windows)]
    #[error("Ошибка Windows: {0}")]
    Windows(String),

    /// macOS не поддерживается
    #[cfg(target_os = "macos")]
    #[error("macOS не поддерживается в текущей версии. Пожалуйста, используйте Linux (X11/Wayland) или Windows.")]
    MacOSUnsupported,

    /// Неизвестная ошибка
    #[error("Неизвестная ошибка: {0}")]
    Unknown(String),
}

impl From<std::io::Error> for PlatformError {
    fn from(err: std::io::Error) -> Self {
        PlatformError::Unknown(err.to_string())
    }
}
