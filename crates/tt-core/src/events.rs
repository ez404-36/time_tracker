//! События и типы данных

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;

use super::pomodoro::PomodoroStatus;

// ============================================================================
// Placeholder типы (будут определены позже в других крейтах)
// ============================================================================

/// Данные об окне
///
/// Примечание: поле `pid` используется только в рантайме для сопоставления окна с процессом.
/// Оно намеренно НЕ персистится в БД (отсутствует в `WindowSession`), так как PID эфемерен:
/// после перезапуска процесса или системы он становится бессмысленным в исторической статистике.
/// Python-версия TimeTracker также не сохраняла PID в БД.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct WindowData {
    /// Имя исполняемого файла процесса
    pub executable_name: String,
    /// Заголовок окна (может отсутствовать)
    pub window_title: Option<String>,
    /// Полный путь к исполняемому файлу (может отсутствовать)
    pub executable_path: Option<String>,
    /// PID процесса (может отсутствовать, не персистится в БД, используется только в рантайме)
    pub pid: Option<u32>,
}

/// Значение настроек (универсальный тип для разных типов данных)
pub type Value = serde_json::Value;

// ============================================================================
// Системные события
// ============================================================================

/// Системные события TimeTracker
///
/// Объединяет тип события и его payload в один enum.
/// Все события отправляются через EventBus и могут обрабатываться
/// несколькими подписчиками.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SystemEvent {
    // ------------------------------------------------------------------------
    // App events (3 события)
    // ------------------------------------------------------------------------
    /// Приложение открылось
    AppOpen { ts: DateTime<Utc> },

    /// Приложение закрывается
    AppClose { ts: DateTime<Utc> },

    /// Изменение настроек приложения
    AppChangeSettings { values: HashMap<String, Value> },

    // ------------------------------------------------------------------------
    // Media events (2 события)
    // ------------------------------------------------------------------------
    /// Добавление медиафайла
    MediaAddFile {
        filename: String,
        path: Option<PathBuf>,
    },

    /// Удаление медиафайла
    MediaDeleteFile {
        filename: String,
        path: Option<PathBuf>,
    },

    // ------------------------------------------------------------------------
    // Main tracker events (4 события)
    // ------------------------------------------------------------------------
    /// Запуск основного трекера
    MainTrackerStart {
        window_tracking: bool,
        idle_tracking: bool,
        pomodoro_tracking: bool,
    },

    /// Пауза основного трекера
    MainTrackerPause,

    /// Приостановка основного трекера (hold)
    MainTrackerHold,

    /// Возобновление работы основного трекера
    MainTrackerResume,

    /// Остановка основного трекера
    MainTrackerStop,

    // ------------------------------------------------------------------------
    // Activity tracker events (4 события)
    // ------------------------------------------------------------------------
    /// Запуск трекера активности
    ActivityTrackerStart,

    /// Остановка трекера активности
    ActivityTrackerStop,

    /// Обнаружение бездействия пользователя
    ActivityTrackerDetectIdle { ts: DateTime<Utc> },

    /// Остановка бездействия пользователя
    ActivityTrackerStopIdle { ts: DateTime<Utc> },

    // ------------------------------------------------------------------------
    // Window tracker events (3 события)
    // ------------------------------------------------------------------------
    /// Запуск трекера окон
    WindowTrackerStart,

    /// Остановка трекера окон
    WindowTrackerStop,

    /// Переключение окна
    WindowTrackerSwitchWindow {
        window: WindowData,
        ts: DateTime<Utc>,
    },

    /// Изменение списка открытых окон
    WindowTrackerChangeOpenedWindows { active_windows: Vec<WindowData> },

    // ------------------------------------------------------------------------
    // Pomodoro tracker events (1 событие)
    // ------------------------------------------------------------------------
    /// Изменение статуса помодоро-таймера
    PomodoroTrackerChangeStatus {
        prev_status: PomodoroStatus,
        new_status: PomodoroStatus,
    },

    // ------------------------------------------------------------------------
    // Tasks events (3 события)
    // ------------------------------------------------------------------------
    /// Добавление задачи
    TasksAdd { task: String },

    /// Обновление задачи
    TasksUpdate { task: String },

    /// Удаление задачи
    TasksDelete { task: String },

    // ------------------------------------------------------------------------
    // Error events (3 события)
    // ------------------------------------------------------------------------
    /// Системная ошибка
    ErrorSystem { source: String, error: String },

    /// Ошибка конфигурации
    ErrorWrongConfig { field: String, error: String },

    /// Файл не найден
    ErrorFileNotFound { filename: String },
}
