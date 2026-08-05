//! tt-db: слой доступа к данным TimeTracker
//!
//! ## Выбор подхода для sqlx compile-time проверки (R4)
//!
//! **Выбран вариант 1**: `cargo sqlx prepare` + коммит `.sqlx/`
//!
//! ### Почему выбран вариант 1:
//! - Compile-time проверка SQL-запросов предотвращает ошибки времени выполнения
//! - В CI собирается на чистом клоне без необходимости в живой БД
//! - Более строгая типобезопасность — ошибка в SQL обнаруживается на этапе сборки
//! - Лучшая документация кода — макросы `query!` явно показывают структуру результата
//!
//! ### Требования:
//! - Установить `sqlx-cli` локально: `cargo install sqlx-cli`
//! - Переменная окружения `DATABASE_URL` должна указывать на действующую БД с миграциями
//! - Запустить `cargo sqlx prepare` перед коммитом
//! - Коммитить директорию `.sqlx/` с метаданными запросов
//!
//! ## Структура крейта
//!
//! - [`models`] — доменные модели (Task, Settings, WindowSession и др.)
//! - [`repositories`] — репозитории для CRUD-операций
//! - [`pool`] — создание пула соединений SQLite в WAL-режиме
//!
//! ## Исправленные баги из Python-версии
//!
//! ### B2: неправильный IN-запрос
//! Исправлен в [`TaskRepository::mark_expired`](repositories::task::TaskRepository::mark_expired)
//!
//! ### B3: неправильное вычисление duration
//! Исправлено в [`SessionRepository`](repositories::session::SessionRepository)
//! - Используется `num_seconds()` вместо `.seconds` для корректной работы с днями
//! - Проверка на отрицательную дельту (возвращает 0 вместо огромного числа)
//!
//! ### B7: неправильное использование Value()
//! Исправлено в [`TaskRepository::get_with_expired_check`](repositories::task::TaskRepository::get_with_expired_check)
//! - Используется SQL `CASE` вместо неправильного оборачивания выражений в `Value()`

pub mod models;
pub mod pool;
pub mod repositories;

pub use pool::{create_pool, PoolError};

// Re-export frequently used types
pub use models::{
    AppStatistics, IdleSession, NewIdleSession, NewSettings, NewSettingsAudioParam, NewTask,
    NewWindowSession, Settings, SettingsAudioParam, Task, UpdateSettings, UpdateSettingsAudioParam,
    UpdateTask, WindowSession,
};

pub use repositories::{
    SessionRepository, SessionRepositoryError, SettingsRepository, SettingsRepositoryError,
    TaskRepository, TaskRepositoryError,
};
