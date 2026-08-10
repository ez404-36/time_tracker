//! Ошибки трекеров

use thiserror::Error;

/// Ошибки трекеров
#[derive(Debug, Error)]
pub enum TrackerError {
    /// Ошибка платформы при получении данных об окнах
    #[error("Ошибка платформы: {0}")]
    Platform(#[from] tt_platform::PlatformError),

    /// Ошибка базы данных
    #[error("Ошибка базы данных: {0}")]
    Database(#[from] tt_db::SessionRepositoryError),

    /// Ошибка репозитория задач
    #[error("Ошибка репозитория задач: {0}")]
    TaskRepository(#[from] tt_db::TaskRepositoryError),

    /// Неверный переход статуса помодоро
    #[error("Неверный переход статуса помодоро: {0} -> {1}")]
    InvalidPomodoroTransition(String, String),

    /// Таймер помодоро не запущен
    #[error("Таймер помодоро не запущен")]
    PomodoroNotRunning,

    /// Настройки не найдены
    #[error("Настройки не найдены")]
    SettingsNotFound,
}
