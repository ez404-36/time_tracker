//! Реализация для Wayland (GNOME только)

#[cfg(all(target_os = "linux", feature = "wayland"))]
use crate::error::PlatformError;
#[cfg(all(target_os = "linux", feature = "wayland"))]
use crate::WindowControl;
#[cfg(all(target_os = "linux", feature = "wayland"))]
use std::env;
#[cfg(all(target_os = "linux", feature = "wayland"))]
use tracing::debug;
#[cfg(all(target_os = "linux", feature = "wayland"))]
use tt_core::WindowData;
#[cfg(all(target_os = "linux", feature = "wayland"))]
use zbus::blocking::Connection;
#[cfg(all(target_os = "linux", feature = "wayland"))]
use zbus::blocking::Proxy;

#[cfg(all(target_os = "linux", feature = "wayland"))]
/// Wayland реализация WindowControl (только GNOME)
pub struct WaylandWindowControl {
    unsafe_mode_enabled: bool,
    connection: Connection,
}

#[cfg(all(target_os = "linux", feature = "wayland"))]
impl WaylandWindowControl {
    /// Создаёт новую Wayland-реализацию
    pub fn new() -> Result<Self, PlatformError> {
        // Проверяем, что мы в Wayland-сессии
        if !Self::is_wayland_session() {
            return Err(PlatformError::WaylandNotSupported(
                "Не Wayland-сессия (проверьте WAYLAND_DISPLAY или XDG_SESSION_TYPE)".to_string(),
            ));
        }

        // Проверяем, что это GNOME
        if !Self::is_gnome() {
            return Err(PlatformError::WaylandNotSupported(
                "Wayland реализация поддерживает только GNOME".to_string(),
            ));
        }

        // Подключаемся к session bus
        let connection = Connection::session()
            .map_err(|e| PlatformError::WaylandNotSupported(format!("D-Bus ошибка: {}", e)))?;

        debug!("Wayland WindowControl инициализирован (GNOME)");

        Ok(Self {
            unsafe_mode_enabled: false, // TODO: читать из настроек
            connection,
        })
    }

    /// Проверяет, что это Wayland-сессия
    fn is_wayland_session() -> bool {
        env::var("WAYLAND_DISPLAY").is_ok()
            || env::var("XDG_SESSION_TYPE").is_ok_and(|v| v == "wayland")
    }

    /// Проверяет, что это GNOME
    fn is_gnome() -> bool {
        if let Ok(desktop) = env::var("XDG_CURRENT_DESKTOP") {
            desktop.to_lowercase().contains("gnome")
        } else {
            false
        }
    }

    /// Получает время бездействия через GNOME IdleMonitor
    fn get_idle_time_wayland(&self) -> Result<u64, PlatformError> {
        let proxy = Proxy::new(
            &self.connection,
            "org.gnome.Mutter.IdleMonitor",
            "/org/gnome/Mutter/IdleMonitor/Core",
            "org.gnome.Mutter.IdleMonitor",
        )?;

        let message = proxy.call_method("GetIdletime", &())?;

        // Получаем body и десериализуем как u64
        let body = message.body();
        let idle_ms: u64 = body.deserialize::<u64>()?;

        Ok(idle_ms / 1000) // конвертируем в секунды
    }
}

#[cfg(all(target_os = "linux", feature = "wayland"))]
impl WindowControl for WaylandWindowControl {
    fn active_window(&self) -> Result<Option<WindowData>, PlatformError> {
        if !self.unsafe_mode_enabled {
            return Err(PlatformError::WaylandUnsafeModeRequired);
        }

        // TODO: реализовать получение активного окна через GNOME Shell
        // Это требует отдельного D-Bus интерфейса или расширения GNOME Shell
        Err(PlatformError::WaylandNotSupported(
            "Получение активного окна в Wayland требует unsafe_mode (TODO)".to_string(),
        ))
    }

    fn all_windows(&self) -> Result<Vec<WindowData>, PlatformError> {
        if !self.unsafe_mode_enabled {
            return Err(PlatformError::WaylandUnsafeModeRequired);
        }

        // TODO: реализовать получение списка окон через GNOME Shell
        Err(PlatformError::WaylandNotSupported(
            "Получение списка окон в Wayland требует unsafe_mode (TODO)".to_string(),
        ))
    }

    fn idle_seconds(&self) -> Result<u64, PlatformError> {
        self.get_idle_time_wayland()
    }
}
