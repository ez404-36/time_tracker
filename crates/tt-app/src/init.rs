//! Инициализация и завершение приложения

use std::path::PathBuf;
use tracing_subscriber::prelude::*;

/// Инициализирует логирование с ретенцией 7 дней
pub fn init_logging() {
    let log_dir = std::env::current_dir()
        .unwrap_or_else(|_| PathBuf::from("."))
        .join("logs");

    std::fs::create_dir_all(&log_dir).ok();

    let file_appender = tracing_appender::rolling::daily(&log_dir, "timetracker.log");
    let (non_blocking, guard) = tracing_appender::non_blocking(file_appender);

    let env_filter = tracing_subscriber::EnvFilter::from_default_env()
        .add_directive(tracing::Level::INFO.into());

    tracing_subscriber::registry()
        .with(env_filter)
        .with(tracing_subscriber::fmt::layer().with_writer(non_blocking))
        .with(tracing_subscriber::fmt::layer().with_writer(std::io::stdout))
        .init();

    std::mem::forget(guard);
}

/// Возвращает путь к базе данных
pub fn get_db_path() -> PathBuf {
    let mut path = std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."));

    path.push("timetracker.db");
    path
}
