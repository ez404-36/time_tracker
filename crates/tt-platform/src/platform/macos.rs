//! Заглушка для macOS (не реализована)

use crate::error::PlatformError;
use crate::WindowControl;
use tt_core::WindowData;

/// macOS реализация WindowControl (заглушка)
pub struct MacosWindowControl;

impl MacosWindowControl {
    /// Создаёт новую macOS-заглушку
    pub fn new() -> Self {
        Self
    }
}

impl WindowControl for MacosWindowControl {
    fn active_window(&self) -> Result<Option<WindowData>, PlatformError> {
        Err(PlatformError::MacOSUnsupported)
    }

    fn all_windows(&self) -> Result<Vec<WindowData>, PlatformError> {
        Err(PlatformError::MacOSUnsupported)
    }

    fn idle_seconds(&self) -> Result<u64, PlatformError> {
        Err(PlatformError::MacOSUnsupported)
    }
}
