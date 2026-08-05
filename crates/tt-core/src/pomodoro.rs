//! Статусы помодоро-таймера

use serde::{Deserialize, Serialize};

/// Статусы помодоро-таймера
///
/// Реализует конечный автомат с предопределёнными переходами.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum PomodoroStatus {
    /// Таймер отключён
    Disabled,
    /// Неизвестный статус (используется как fallback)
    Unknown,
    /// Рабочий режим: активен
    Working,
    /// Рабочий режим: на паузе
    WorkingPause,
    /// Рабочий режим: завершён
    WorkingStop,
    /// Режим отдыха: активен
    Resting,
    /// Режим отдыха: на паузе
    RestingPause,
    /// Режим отдыха: завершён
    RestingStop,
}

impl PomodoroStatus {
    /// Проверяет, возможен ли переход из текущего статуса в указанный
    ///
    /// # Карта разрешённых переходов:
    /// - `Disabled` → `Working`
    /// - `Working` → `WorkingPause`, `WorkingStop`
    /// - `WorkingPause` → `Working`
    /// - `WorkingStop` → `Resting`
    /// - `Resting` → `RestingPause`, `RestingStop`
    /// - `RestingPause` → `Resting`
    /// - `RestingStop` → `Working`
    /// - Любой статус (кроме Disabled и Unknown) → `Disabled` (через метод stop())
    ///
    /// Переходы в/из `Unknown` не разрешены.
    #[must_use]
    pub fn can_move_to(&self, next: Self) -> bool {
        match (self, next) {
            (Self::Disabled, Self::Working) => true,
            (Self::Working, Self::WorkingPause | Self::WorkingStop) => true,
            (Self::WorkingPause, Self::Working) => true,
            (Self::WorkingStop, Self::Resting) => true,
            (Self::Resting, Self::RestingPause | Self::RestingStop) => true,
            (Self::RestingPause, Self::Resting) => true,
            (Self::RestingStop, Self::Working) => true,
            // Из любого статуса (кроме Disabled и Unknown) в Disabled разрешён через stop()
            (
                Self::Working
                | Self::WorkingPause
                | Self::WorkingStop
                | Self::Resting
                | Self::RestingPause
                | Self::RestingStop,
                Self::Disabled,
            ) => true,
            _ => false,
        }
    }
}
