//! Модели домена tt-db, идентичные схеме базы данных

use chrono::{DateTime, NaiveDate, NaiveTime, Utc};
use serde::{Deserialize, Serialize};
use sqlx::FromRow;

/// Задача с дедлайном
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Task {
    pub id: Option<i64>,
    pub title: String,
    pub description: Option<String>,
    pub created_at: DateTime<Utc>,
    pub parent_id: Option<i64>,
    pub deadline_date: Option<NaiveDate>,
    pub deadline_time: Option<NaiveTime>,
    pub is_done: bool,
    pub is_expired: bool,
}

/// Новая задача для создания (без id)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NewTask {
    pub title: String,
    pub description: Option<String>,
    pub created_at: DateTime<Utc>,
    pub parent_id: Option<i64>,
    pub deadline_date: Option<NaiveDate>,
    pub deadline_time: Option<NaiveTime>,
    pub is_done: bool,
    pub is_expired: bool,
}

/// Обновление задачи (все поля опциональны)
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct UpdateTask {
    pub title: Option<String>,
    pub description: Option<String>,
    pub parent_id: Option<Option<i64>>,
    pub deadline_date: Option<Option<NaiveDate>>,
    pub deadline_time: Option<Option<NaiveTime>>,
    pub is_done: Option<bool>,
    pub is_expired: Option<bool>,
}

/// Сессия активности в окне приложения
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct WindowSession {
    pub id: Option<i64>,
    pub start_ts: DateTime<Utc>,
    pub end_ts: Option<DateTime<Utc>>,
    pub duration: i64,
    pub executable_name: String,
    pub executable_path: Option<String>,
    pub window_title: Option<String>,
}

/// Новая сессия окна для создания
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NewWindowSession {
    pub start_ts: DateTime<Utc>,
    pub end_ts: Option<DateTime<Utc>>,
    pub duration: i64,
    pub executable_name: String,
    pub executable_path: Option<String>,
    pub window_title: Option<String>,
}

/// Сессия бездействия пользователя
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct IdleSession {
    pub id: Option<i64>,
    pub start_ts: DateTime<Utc>,
    pub end_ts: Option<DateTime<Utc>>,
    pub duration: i64,
}

/// Новая сессия бездействия для создания
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NewIdleSession {
    pub start_ts: DateTime<Utc>,
    pub end_ts: Option<DateTime<Utc>>,
    pub duration: i64,
}

/// Статистика по приложениям за день
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppStatistics {
    pub executable_name: String,
    pub total_duration: i64,
    pub session_count: i64,
}

/// Настройки приложения (singleton)
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Settings {
    pub id: Option<i64>,
    pub client_timezone: String,
    pub idle_threshold: i32,
    pub enable_window_tracking: bool,
    pub enable_idle_tracking: bool,
    pub enable_pomodoro: bool,
    pub pomodoro_work_time: Option<i16>,
    pub pomodoro_rest_time: Option<i16>,
    pub ui_settings: serde_json::Value,
    pub task_deadline_sound_config_id: Option<i64>,
    pub idle_sound_config_id: Option<i64>,
    pub pomodoro_sound_config_id: Option<i64>,
    pub autostart_enabled: bool,
    pub start_minimized: bool,
    pub close_to_tray: bool,
    pub autostart_tracking: bool,
}

/// Новые настройки для создания
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NewSettings {
    pub client_timezone: String,
    pub idle_threshold: i32,
    pub enable_window_tracking: bool,
    pub enable_idle_tracking: bool,
    pub enable_pomodoro: bool,
    pub pomodoro_work_time: Option<i16>,
    pub pomodoro_rest_time: Option<i16>,
    pub ui_settings: serde_json::Value,
    pub task_deadline_sound_config_id: Option<i64>,
    pub idle_sound_config_id: Option<i64>,
    pub pomodoro_sound_config_id: Option<i64>,
    pub autostart_enabled: bool,
    pub start_minimized: bool,
    pub close_to_tray: bool,
    pub autostart_tracking: bool,
}

/// Обновление настроек (все поля опциональны)
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct UpdateSettings {
    pub client_timezone: Option<String>,
    pub idle_threshold: Option<i32>,
    pub enable_window_tracking: Option<bool>,
    pub enable_idle_tracking: Option<bool>,
    pub enable_pomodoro: Option<bool>,
    pub pomodoro_work_time: Option<Option<i16>>,
    pub pomodoro_rest_time: Option<Option<i16>>,
    pub ui_settings: Option<serde_json::Value>,
    pub task_deadline_sound_config_id: Option<Option<i64>>,
    pub idle_sound_config_id: Option<Option<i64>>,
    pub pomodoro_sound_config_id: Option<Option<i64>>,
    pub autostart_enabled: Option<bool>,
    pub start_minimized: Option<bool>,
    pub close_to_tray: Option<bool>,
    pub autostart_tracking: Option<bool>,
}

/// Параметры звукового уведомления
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct SettingsAudioParam {
    pub id: Option<i64>,
    pub disabled: bool,
    pub sound: Option<String>,
    pub volume_offset: f64,
}

/// Новые параметры звука для создания
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NewSettingsAudioParam {
    pub disabled: bool,
    pub sound: Option<String>,
    pub volume_offset: f64,
}

/// Обновление параметров звука
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct UpdateSettingsAudioParam {
    pub disabled: Option<bool>,
    pub sound: Option<Option<String>>,
    pub volume_offset: Option<f64>,
}
