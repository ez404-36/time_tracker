//! Пул соединений SQLite в WAL-режиме

use sqlx::{sqlite::SqliteConnectOptions, SqlitePool};
use std::str::FromStr;
use thiserror::Error;

/// Ошибки при работе с пулом соединений
#[derive(Debug, Error)]
pub enum PoolError {
    #[error("Ошибка подключения к базе данных: {0}")]
    Connection(#[from] sqlx::Error),

    #[error("Ошибка миграции: {0}")]
    Migration(#[from] sqlx::migrate::MigrateError),
}

/// Создаёт пул соединений с SQLite в WAL-режиме
///
/// # Параметры
/// - `database_url`: путь к файлу БД или `:memory:` для in-memory
///
/// # Особенности
/// - WAL-режим для параллельного чтения/записи
/// - Автоматическое применение миграций
pub async fn create_pool(database_url: &str) -> Result<SqlitePool, PoolError> {
    let options = SqliteConnectOptions::from_str(database_url)?
        .create_if_missing(true)
        .pragma("journal_mode", "WAL") // WAL-режим
        .pragma("synchronous", "NORMAL")
        .pragma("foreign_keys", "true") // Включаем FK
        .pragma("cache_size", "10000")
        .pragma("temp_store", "memory");

    let pool = SqlitePool::connect_with(options).await?;

    // Применяем миграции
    sqlx::migrate!("./migrations").run(&pool).await?;

    Ok(pool)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_create_pool_in_memory() {
        let pool = create_pool(":memory:").await.unwrap();

        // Проверяем, что таблицы созданы
        let result: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM task")
            .fetch_one(&pool)
            .await
            .unwrap();
        assert_eq!(result.0, 0);

        pool.close().await;
    }

    #[tokio::test]
    async fn test_create_pool_tempfile() {
        let pool = create_pool(":memory:").await.unwrap();

        // Проверяем, что пул работает
        let result: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM task")
            .fetch_one(&pool)
            .await
            .unwrap();
        assert_eq!(result.0, 0);

        pool.close().await;
    }
}
