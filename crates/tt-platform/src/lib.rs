//! tt-platform: контроль активных окон и бездействия пользователя
//!
//! Платформо-независимый интерфейс для получения информации об активных окнах
//! и отслеживания бездействия пользователя на различных операционных системах.
//!
//! ## Особенности
//!
//! - **Linux/X11**: работа через x11rb (без внешних зависимостей)
//! - **Linux/Wayland**: работа через zbus (D-Bus для GNOME)
//! - **Windows**: работа через WinAPI + sysinfo
//! - **macOS**: заглушка с явной ошибкой (требуется отдельная реализация)
//!
//! ## Трансформация заголовков окон
//!
//! Поддерживаются трансформеры для:
//! - Telegram Desktop (удаление счётчика непрочитанных)
//! - Яндекс Браузер (удаление суффиксов)
//! - Steam игры (извлечение названия игры)

mod error;
mod platform;
mod transformers;

use tt_core::WindowData;

// Re-экспорты для публичного API
pub use error::PlatformError;
pub use transformers::{transform_title_and_app_name, TitleTransformer};

// Платформо-специфичные реализации (re-экспорты через cfg)
#[cfg(target_os = "linux")]
pub use platform::linux::LinuxWindowControl;

#[cfg(windows)]
pub use platform::windows::WindowsWindowControl;

#[cfg(target_os = "macos")]
pub use platform::macos::MacosWindowControl;

/// Базовый trait для контроля окон и бездействия
///
/// Этот trait предоставляет платформо-независимый интерфейс для:
/// - получения активного окна
/// - получения списка всех окон
/// - отслеживания времени бездействия пользователя
pub trait WindowControl: Send + Sync {
    /// Возвращает данные об активном окне
    ///
    /// # Returns
    ///
    /// - `Ok(Some(WindowData))` — активное окно найдено
    /// - `Ok(None)` — нет активного окна (например, на пустом рабочем столе)
    /// - `Err(PlatformError)` — ошибка при получении данных
    fn active_window(&self) -> Result<Option<WindowData>, PlatformError>;

    /// Возвращает список всех видимых окон
    ///
    /// # Returns
    ///
    /// - `Ok(Vec<WindowData>)` — список всех видимых окон
    /// - `Err(PlatformError)` — ошибка при получении данных
    fn all_windows(&self) -> Result<Vec<WindowData>, PlatformError>;

    /// Возвращает время бездействия пользователя в секундах
    ///
    /// # Returns
    ///
    /// - `Ok(seconds)` — время бездействия в секундах
    /// - `Err(PlatformError)` — ошибка при получении данных
    fn idle_seconds(&self) -> Result<u64, PlatformError>;
}

/// Создаёт платформо-специфичную реализацию WindowControl
///
/// Эта функция автоматически определяет текущую платформу и тип сессии
/// (X11/Wayland на Linux) и возвращает соответствующую реализацию.
///
/// # Errors
///
/// - Возвращает `PlatformError::Unsupported` если платформа не поддерживается
/// - Возвращает `PlatformError::WaylandNotSupported` если Wayland недоступен
/// - Возвращает `PlatformError::WaylandUnsafeModeRequired` если требуется unsafe_mode
pub fn create_window_control() -> Result<Box<dyn WindowControl>, PlatformError> {
    #[cfg(target_os = "linux")]
    {
        platform::linux::create_linux_window_control()
    }

    #[cfg(windows)]
    {
        Ok(Box::new(WindowsWindowControl::new()))
    }

    #[cfg(target_os = "macos")]
    {
        Ok(Box::new(MacosWindowControl::new()))
    }

    #[cfg(not(any(target_os = "linux", windows, target_os = "macos")))]
    {
        Err(PlatformError::Unsupported {
            platform: std::env::consts::OS.to_string(),
        })
    }
}
