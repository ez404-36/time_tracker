//! tt-tracker: сервисы отслеживания активности — Main/Window/Idle/Pomodoro/Deadline.
//!
//! Этап 6.
//!
//! ## Архитектура
//!
//! Крейт содержит сервисы, которые отслеживают активность пользователя:
//!
//! - [`MainTracker`] — оркестратор всех трекеров, публикует события старта/остановки
//! - [`WindowTracker`] — отслеживает активное окно и список открытых окон
//! - [`IdleTracker`] — отслеживает бездействие пользователя
//! - [`PomodoroTracker`] — управляет таймером помодоро (таймер живёт в сервисе!)
//! - [`DeadlineChecker`] — периодически проверяет задачи с истёкшим дедлайном
//!
//! ## Исправленные баги из Python-версии
//!
//! ### B1: неправильное сравнение списков окон
//! Исправлено в [`WindowTracker::_tick`] — корректное сравнение множеств через хеш-структуры.
//!
//! ### B3: неправильное вычисление duration
//! Исправлено в вычислении длительности сессий — используется `num_seconds()` вместо `.seconds`.
//!
//! ### B7: неправильное использование Value()
//! Исправлено в [`DeadlineChecker`] — используется корректная логика проверки дедлайнов.
//!
//! ## Логирование
//!
//! Вместо записи событий в таблицу `event` (как в Python-версии) используется структурированное
//! логирование через `tracing`. Логи пишутся в файлы с суточной ротацией и ретенцией 7 дней.

pub mod deadline_checker;
pub mod error;
pub mod idle_tracker;
pub mod logging;
pub mod main_tracker;
pub mod pomodoro_tracker;
pub mod window_tracker;

pub use deadline_checker::DeadlineChecker;
pub use error::TrackerError;
pub use idle_tracker::IdleTracker;
pub use main_tracker::MainTracker;
pub use pomodoro_tracker::PomodoroTracker;
pub use window_tracker::WindowTracker;

/// Возвращает версию крейта
#[must_use]
pub fn version() -> &'static str {
    "0.1.0"
}
