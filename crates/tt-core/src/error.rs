//! Ошибки ядра

use super::pomodoro::PomodoroStatus;
use thiserror::Error;
use tokio::sync::broadcast;

/// Ошибки ядра tt-core
#[derive(Debug, Error)]
pub enum CoreError {
    /// Недопустимый переход помодоро-таймера
    #[error("Invalid Pomodoro transition: {from:?} → {to:?}")]
    InvalidPomodoroTransition {
        from: PomodoroStatus,
        to: PomodoroStatus,
    },

    /// Ошибка шины событий (проскачивание сообщений)
    #[error("Event bus lagged: {0}")]
    EventBusLagged(#[from] broadcast::error::RecvError),

    /// Ошибка сериализации
    #[error("Serialization error: {0}")]
    Serialization(String),

    /// Ошибка десериализации
    #[error("Deserialization error: {0}")]
    Deserialization(String),
}
