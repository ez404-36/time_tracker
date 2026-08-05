//! Реализация для X11 через x11rb

#[cfg(all(target_os = "linux", feature = "x11"))]
use crate::error::PlatformError;
#[cfg(all(target_os = "linux", feature = "x11"))]
use crate::WindowControl;
#[cfg(all(target_os = "linux", feature = "x11"))]
use tracing::{debug, warn};
#[cfg(all(target_os = "linux", feature = "x11"))]
use tt_core::WindowData;
#[cfg(all(target_os = "linux", feature = "x11"))]
use x11rb::connection::Connection;
#[cfg(all(target_os = "linux", feature = "x11"))]
use x11rb::protocol::screensaver::ConnectionExt as _;
#[cfg(all(target_os = "linux", feature = "x11"))]
use x11rb::protocol::xproto::*;
#[cfg(all(target_os = "linux", feature = "x11"))]
use x11rb::rust_connection::RustConnection;

#[cfg(all(target_os = "linux", feature = "x11"))]
/// Атомы EWMH/NetWM
#[derive(Debug, Clone, Copy)]
struct EwmhAtoms {
    _net_active_window: Atom,
    _net_client_list: Atom,
    _net_wm_pid: Atom,
    _net_wm_name: Atom,
    utf8_string: Atom,
}

#[cfg(all(target_os = "linux", feature = "x11"))]
/// X11 реализация WindowControl
pub struct X11WindowControl {
    conn: RustConnection,
    root: Window,
    atoms: EwmhAtoms,
}

#[cfg(all(target_os = "linux", feature = "x11"))]
impl X11WindowControl {
    /// Создаёт новую X11-реализацию
    pub fn new() -> Result<Self, PlatformError> {
        // Проверяем переменную DISPLAY
        if std::env::var("DISPLAY").is_err() {
            return Err(PlatformError::X11NotAvailable);
        }

        let (conn, _screen_num) = x11rb::connect(None)
            .map_err(|e| PlatformError::Unknown(format!("X11 connection error: {:?}", e)))?;

        let screen = &conn.setup().roots[_screen_num];
        let root = screen.root;

        // Получаем атомы EWMH
        let atoms = Self::init_atoms(&conn)?;

        debug!("X11 WindowControl инициализирован");

        Ok(Self { conn, root, atoms })
    }

    /// Инициализирует атомы EWMH
    fn init_atoms(conn: &RustConnection) -> Result<EwmhAtoms, PlatformError> {
        // Получаем атомы по одному, чтобы избежать проблем с массивами разной длины
        let active_window_cookie = conn
            .intern_atom(false, b"_NET_ACTIVE_WINDOW")
            .map_err(|e| {
                PlatformError::Unknown(format!("Failed to create intern atom cookie: {:?}", e))
            })?;
        let client_list_cookie = conn.intern_atom(false, b"_NET_CLIENT_LIST").map_err(|e| {
            PlatformError::Unknown(format!("Failed to create intern atom cookie: {:?}", e))
        })?;
        let wm_pid_cookie = conn.intern_atom(false, b"_NET_WM_PID").map_err(|e| {
            PlatformError::Unknown(format!("Failed to create intern atom cookie: {:?}", e))
        })?;
        let wm_name_cookie = conn.intern_atom(false, b"_NET_WM_NAME").map_err(|e| {
            PlatformError::Unknown(format!("Failed to create intern atom cookie: {:?}", e))
        })?;
        let utf8_string_cookie = conn.intern_atom(false, b"UTF8_STRING").map_err(|e| {
            PlatformError::Unknown(format!("Failed to create intern atom cookie: {:?}", e))
        })?;

        let _net_active_window = active_window_cookie
            .reply()
            .map_err(|e| {
                PlatformError::Unknown(format!("Failed to intern _NET_ACTIVE_WINDOW: {:?}", e))
            })?
            .atom;
        let _net_client_list = client_list_cookie
            .reply()
            .map_err(|e| {
                PlatformError::Unknown(format!("Failed to intern _NET_CLIENT_LIST: {:?}", e))
            })?
            .atom;
        let _net_wm_pid = wm_pid_cookie
            .reply()
            .map_err(|e| PlatformError::Unknown(format!("Failed to intern _NET_WM_PID: {:?}", e)))?
            .atom;
        let _net_wm_name = wm_name_cookie
            .reply()
            .map_err(|e| PlatformError::Unknown(format!("Failed to intern _NET_WM_NAME: {:?}", e)))?
            .atom;
        let utf8_string = utf8_string_cookie
            .reply()
            .map_err(|e| PlatformError::Unknown(format!("Failed to intern UTF8_STRING: {:?}", e)))?
            .atom;

        Ok(EwmhAtoms {
            _net_active_window,
            _net_client_list,
            _net_wm_pid,
            _net_wm_name,
            utf8_string,
        })
    }

    /// Получает значение свойства окна
    fn get_window_property(
        &self,
        window: Window,
        property: Atom,
        property_type: Atom,
    ) -> Result<Option<Vec<u8>>, PlatformError> {
        let cookie = self
            .conn
            .get_property(false, window, property, property_type, 0, u32::MAX)
            .map_err(|_e| PlatformError::X11PropertyError {
                property: property.to_string(),
            })?;
        let reply = cookie
            .reply()
            .map_err(|_e| PlatformError::X11PropertyError {
                property: property.to_string(),
            })?;

        if reply.type_ != property_type {
            return Ok(None);
        }

        Ok(Some(reply.value))
    }

    /// Получает PID процесса окна
    fn get_window_pid(&self, window: Window) -> Option<u32> {
        match self.get_window_property(window, self.atoms._net_wm_pid, Atom::from(0u32)) {
            Ok(Some(data)) => {
                if data.len() >= 4 {
                    let pid = u32::from_ne_bytes([data[0], data[1], data[2], data[3]]);
                    Some(pid)
                } else {
                    None
                }
            }
            _ => None,
        }
    }

    /// Получает заголовок окна (NET_WM_NAME)
    fn get_window_title(&self, window: Window) -> Option<String> {
        // Сначала пробуем UTF8_STRING
        if let Ok(Some(data)) =
            self.get_window_property(window, self.atoms._net_wm_name, self.atoms.utf8_string)
        {
            if let Ok(title) = String::from_utf8(data) {
                return Some(title);
            }
        }

        // Fallback на WM_NAME (текст)
        let cookie = self.conn.get_property(
            false,
            window,
            AtomEnum::WM_NAME,
            AtomEnum::STRING,
            0,
            u32::MAX,
        );

        if let Ok(cookie) = cookie {
            if let Ok(reply) = cookie.reply() {
                if reply.type_ == u32::from(AtomEnum::STRING) {
                    if let Ok(title) = String::from_utf8(reply.value) {
                        return Some(title);
                    }
                }
            }
        }

        None
    }

    /// Получает имя процесса по PID
    fn get_process_name(&self, pid: u32) -> Option<String> {
        // Читаем /proc/[pid]/comm
        let comm_path = format!("/proc/{}/comm", pid);
        if let Ok(content) = std::fs::read_to_string(&comm_path) {
            Some(content.trim().to_string())
        } else {
            None
        }
    }

    /// Получает путь к исполняемому файлу процесса по PID
    fn get_process_path(&self, pid: u32) -> Option<String> {
        // Читаем /proc/[pid]/exe
        let exe_path = format!("/proc/{}/exe", pid);
        if let Ok(path) = std::fs::read_link(&exe_path) {
            path.to_str().map(|s| s.to_string())
        } else {
            None
        }
    }

    /// Получает данные окна
    fn get_window_data(&self, window: Window) -> Option<WindowData> {
        let pid = self.get_window_pid(window)?;
        let title = self.get_window_title(window);
        let executable_name = self
            .get_process_name(pid)
            .unwrap_or_else(|| "unknown".to_string());
        let executable_path = self.get_process_path(pid);

        Some(WindowData {
            executable_name,
            window_title: title,
            executable_path,
            pid: Some(pid),
        })
    }

    /// Получает активное окно
    fn get_active_window_xid(&self) -> Result<Option<Window>, PlatformError> {
        match self.get_window_property(self.root, self.atoms._net_active_window, Atom::from(0u32)) {
            Ok(Some(data)) => {
                if data.len() >= 4 {
                    let window = u32::from_ne_bytes([data[0], data[1], data[2], data[3]]);
                    Ok(Some(window))
                } else {
                    Ok(None)
                }
            }
            Ok(None) => Ok(None),
            Err(e) => Err(e),
        }
    }

    /// Получает список всех окон
    fn get_client_list(&self) -> Result<Vec<Window>, PlatformError> {
        match self.get_window_property(self.root, self.atoms._net_client_list, Atom::from(0u32)) {
            Ok(Some(data)) => {
                let windows: Vec<Window> = data
                    .chunks_exact(4)
                    .filter_map(|chunk| {
                        if chunk.len() == 4 {
                            Some(u32::from_ne_bytes([chunk[0], chunk[1], chunk[2], chunk[3]]))
                        } else {
                            None
                        }
                    })
                    .collect();

                Ok(windows)
            }
            Ok(None) => Ok(vec![]),
            Err(e) => Err(e),
        }
    }

    /// Получает время бездействия через MIT-SCREEN-SAVER
    fn get_idle_time_x11(&self) -> Result<u64, PlatformError> {
        // Проверяем наличие расширения MIT-SCREEN-SAVER
        let cookie = self
            .conn
            .query_extension(b"MIT-SCREEN-SAVER")
            .map_err(|e| PlatformError::Unknown(format!("Failed to query extension: {:?}", e)))?;
        let reply = cookie.reply().map_err(|e| {
            PlatformError::Unknown(format!("Failed to query extension reply: {:?}", e))
        })?;

        if !reply.present {
            warn!("Расширение MIT-SCREEN-SAVER недоступно");
            return Err(PlatformError::Unknown(
                "Расширение MIT-SCREEN-SAVER недоступно".to_string(),
            ));
        }

        // Получаем idle time
        let cookie = self.conn.screensaver_query_info(self.root).map_err(|e| {
            PlatformError::Unknown(format!("Failed to query screensaver info: {:?}", e))
        })?;
        let reply = cookie.reply().map_err(|e| {
            PlatformError::Unknown(format!("Failed to query screensaver info reply: {:?}", e))
        })?;

        // reply.ms_since_user_input - время в миллисекундах
        let idle_ms = reply.ms_since_user_input as u64;
        Ok(idle_ms / 1000) // конвертируем в секунды
    }
}

#[cfg(all(target_os = "linux", feature = "x11"))]
impl WindowControl for X11WindowControl {
    fn active_window(&self) -> Result<Option<WindowData>, PlatformError> {
        let window_xid = self.get_active_window_xid()?;

        match window_xid {
            Some(window) => {
                let window_data = self.get_window_data(window);
                Ok(window_data)
            }
            None => Ok(None),
        }
    }

    fn all_windows(&self) -> Result<Vec<WindowData>, PlatformError> {
        let windows = self.get_client_list()?;

        let mut result = Vec::new();
        for window in windows {
            if let Some(data) = self.get_window_data(window) {
                // Фильтруем окна без заголовка (обычно это системные окна)
                if data.window_title.is_some() {
                    result.push(data);
                }
            }
        }

        Ok(result)
    }

    fn idle_seconds(&self) -> Result<u64, PlatformError> {
        self.get_idle_time_x11()
    }
}
