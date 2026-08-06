//! Реализация для Windows через WinAPI + sysinfo

use crate::error::PlatformError;
use crate::WindowControl;
use sysinfo::{Pid, System, ProcessesToUpdate, ProcessRefreshKind};
use tracing::debug;
use tt_core::WindowData;
use windows::core::*;
use windows::Win32::Foundation::*;
use windows::Win32::UI::WindowsAndMessaging::*;

#[repr(C)]
#[derive(Default)]
struct LASTINPUTINFO {
    cbSize: u32,
    dwTime: u32,
}

extern "system" {
    fn GetLastInputInfo(plii: *mut LASTINPUTINFO) -> BOOL;
    fn GetTickCount() -> u32;
}

/// Windows реализация WindowControl
pub struct WindowsWindowControl;

impl WindowsWindowControl {
    /// Создаёт новую Windows-реализацию
    pub fn new() -> Self {
        debug!("Windows WindowControl инициализирован");
        Self
    }

    /// Получает информацию о процессе по PID
    fn get_process_info(system: &mut System, pid: u32) -> Option<(String, Option<String>)> {
        system.refresh_processes(ProcessesToUpdate::Some(&[Pid::from_u32(pid)]), ProcessRefreshKind::new());
        
        if let Some(process) = system.process(Pid::from_u32(pid)) {
            let name = process.name().to_string_lossy().to_string();
            let exe = process.exe().map(|p| p.to_string_lossy().to_string());
            Some((name, exe))
        } else {
            None
        }
    }

    /// Callback для EnumWindows
    unsafe extern "system" fn enum_windows_callback(hwnd: HWND, lparam: LPARAM) -> BOOL {
        let windows = &mut *(lparam.0 as *mut Vec<WindowData>);
        let system_ptr =
            (lparam.0 as usize + std::mem::size_of::<Vec<WindowData>>()) as *mut System;

        // Проверяем, что окно видимое
        if !IsWindowVisible(hwnd).as_bool() {
            return TRUE;
        }

        // Получаем заголовок окна
        let mut title = [0u16; 512];
        let len = GetWindowTextW(hwnd, &mut title);
        if len == 0 {
            return TRUE; // Пропускаем окна без заголовка
        }

        let window_title = String::from_utf16_lossy(&title[..len as usize]);
        if window_title.trim().is_empty() {
            return TRUE;
        }

        // Получаем PID процесса
        let mut pid: u32 = 0;
        GetWindowThreadProcessId(hwnd, Some(&mut pid));

        if pid == 0 {
            return TRUE;
        }

        // Получаем информацию о процессе
        let system = &mut *system_ptr;
        if let Some((executable_name, executable_path)) = system.get_process_info(pid) {
            windows.push(WindowData {
                executable_name,
                window_title: Some(window_title),
                executable_path,
                pid: Some(pid),
            });
        }

        TRUE // Продолжаем перечисление
    }

    /// Перечисляет все окна
    fn enumerate_windows(&mut self) -> Vec<WindowData> {
        let mut windows = Vec::new();
        let system_ptr = &mut self.system as *mut System;

        unsafe {
            // Создаём структуру с указателем на вектор и системой
            let mut data = (windows.as_mut_ptr() as usize, system_ptr as usize);

            EnumWindows(
                Some(Self::enum_windows_callback),
                LPARAM(&mut data as *mut (usize, usize) as isize),
            );
        }

        windows
    }
}

impl WindowControl for WindowsWindowControl {
    fn active_window(&self) -> std::result::Result<Option<WindowData>, PlatformError> {
        let mut system = System::new_all();
        system.refresh_processes(ProcessesToUpdate::All, ProcessRefreshKind::new());

        unsafe {
            // Получаем хэндл активного окна
            let hwnd = GetForegroundWindow();
            if hwnd.is_invalid() {
                return Ok(None);
            }

            // Получаем заголовок окна
            let mut title = [0u16; 512];
            let len = GetWindowTextW(hwnd, &mut title);
            if len == 0 {
                return Ok(None);
            }

            let window_title = String::from_utf16_lossy(&title[..len as usize]);

            // Получаем PID процесса
            let mut pid: u32 = 0;
            GetWindowThreadProcessId(hwnd, Some(&mut pid));

            if pid == 0 {
                return Err(PlatformError::WindowsApi(
                    "Не удалось получить PID процесса".to_string(),
                ));
            }

            // Получаем информацию о процессе
            if let Some((executable_name, executable_path)) = Self::get_process_info(&mut system, pid) {
                Ok(Some(WindowData {
                    executable_name,
                    window_title: Some(window_title),
                    executable_path,
                    pid: Some(pid),
                }))
            } else {
                Err(PlatformError::ProcessNotFound(pid))
            }
        }
    }

    fn all_windows(&self) -> std::result::Result<Vec<WindowData>, PlatformError> {
        let mut system = System::new_all();
        system.refresh_processes(ProcessesToUpdate::All, ProcessRefreshKind::new());

        let mut windows = Vec::new();

        unsafe {
            let mut callback_data = EnumWindowsData {
                windows: Vec::new(),
                system: &mut system,
            };

            EnumWindows(
                Some(Self::enum_windows_callback_struct),
                LPARAM(&mut callback_data as *mut EnumWindowsData as isize),
            );

            Ok(callback_data.windows)
        }
    }

    fn idle_seconds(&self) -> std::result::Result<u64, PlatformError> {
        unsafe {
            let mut lii = LASTINPUTINFO {
                cbSize: std::mem::size_of::<LASTINPUTINFO>() as u32,
                ..Default::default()
            };

            if GetLastInputInfo(&mut lii).as_bool() {
                let tick_count = GetTickCount();
                let idle_ms = tick_count.saturating_sub(lii.dwTime);
                Ok(idle_ms as u64 / 1000) // конвертируем в секунды
            } else {
                Err(PlatformError::WindowsApi(
                    "GetLastInputInfo failed".to_string(),
                ))
            }
        }
    }
}

// Структура для передачи данных в callback
struct EnumWindowsData<'a> {
    windows: Vec<WindowData>,
    system: &'a mut System,
}

impl WindowsWindowControl {
    /// Упрощенный callback для EnumWindows с использованием структуры данных
    unsafe extern "system" fn enum_windows_callback_struct(hwnd: HWND, lparam: LPARAM) -> BOOL {
        let data = &mut *(lparam.0 as *mut EnumWindowsData);

        // Проверяем, что окно видимое
        if !IsWindowVisible(hwnd).as_bool() {
            return TRUE;
        }

        // Получаем заголовок окна
        let mut title = [0u16; 512];
        let len = GetWindowTextW(hwnd, &mut title);
        if len == 0 {
            return TRUE; // Пропускаем окна без заголовка
        }

        let window_title = String::from_utf16_lossy(&title[..len as usize]);
        if window_title.trim().is_empty() {
            return TRUE;
        }

        // Получаем PID процесса
        let mut pid: u32 = 0;
        GetWindowThreadProcessId(hwnd, Some(&mut pid));

        if pid == 0 {
            return TRUE;
        }

        // Получаем информацию о процессе
        data.system.refresh_processes(ProcessesToUpdate::Some(&[Pid::from_u32(pid)]), ProcessRefreshKind::new());
        if let Some((executable_name, executable_path)) = Self::get_process_info(data.system, pid) {
            data.windows.push(WindowData {
                executable_name,
                window_title: Some(window_title),
                executable_path,
                pid: Some(pid),
            });
        }

        TRUE // Продолжаем перечисление
    }

    /// Временный stub для старого callback
    unsafe extern "system" fn enum_windows_callback_simple(hwnd: HWND, _lparam: LPARAM) -> BOOL {
        // Проверяем, что окно видимое
        if !IsWindowVisible(hwnd).as_bool() {
            return TRUE;
        }
        TRUE
    }
}
