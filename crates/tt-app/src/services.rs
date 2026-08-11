//! Интеграция с сервисами трекера
//!
//! В текущей версии tt-app работает с Dioxus 0.7, который имеет свой async runtime.
//! Полноценная интеграция с Tokio-based сервисами (tt-tracker) требует
//! либо перехода на отдельный backend-процесс с IPC, либо использования
//! async-compatible wrapper.
//!
//! Для текущего этапа (фундамент UI) реализуем заглушку, которая:
//! - Инициализирует БД и применяет миграции
//! - Создаёт репозитории для будущей интеграции
//! - Позволяет легко подключить реальную интеграцию в будущем

use std::sync::Arc;
use tracing::{info, warn};
use tt_db::{create_pool, SessionRepository, SettingsRepository, TaskRepository};

/// Ошибка интеграции сервисов
#[derive(Debug)]
pub enum ServicesInitError {
    /// Ошибка создания пула БД
    Database(String),
}

impl std::fmt::Display for ServicesInitError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Database(msg) => write!(f, "Ошибка БД: {}", msg),
        }
    }
}

impl std::error::Error for ServicesInitError {}

/// Контейнер сервисов приложения
///
/// В текущей версии содержит только репозитории БД.
/// Полноценная интеграция с tt-tracker будет добавлена в будущих этапах.
pub struct AppServices {
    pub session_repository: Arc<SessionRepository>,
    pub settings_repository: Arc<SettingsRepository>,
    pub task_repository: Arc<TaskRepository>,
}

impl AppServices {
    /// Инициализирует сервисы приложения
    ///
    /// Создаёт пул БД и репозитории для работы с данными.
    /// В будущих версиях здесь также будет инициализация tt-tracker.
    pub async fn init(db_path: &str) -> Result<Self, ServicesInitError> {
        info!("Инициализация сервисов приложения (базовая версия)");

        info!("Создание пула БД");
        let pool = create_pool(db_path)
            .await
            .map_err(|e| ServicesInitError::Database(e.to_string()))?;

        info!("Применение миграций БД");
        sqlx::query("PRAGMA foreign_keys = ON")
            .execute(&pool)
            .await
            .map_err(|e| ServicesInitError::Database(e.to_string()))?;

        info!("Создание репозиториев");
        let session_repository = Arc::new(SessionRepository::new(pool.clone()));
        let settings_repository = Arc::new(SettingsRepository::new(pool.clone()));
        let task_repository = Arc::new(TaskRepository::new(pool));

        info!("Проверка настроек");
        let _settings = settings_repository.get_or_create().await.map_err(|e| {
            warn!("Не удалось прочитать настройки: {}", e);
            ServicesInitError::Database(format!("Не удалось прочитать настройки: {}", e))
        })?;

        info!("Сервисы инициализированы успешно");

        Ok(Self {
            session_repository,
            settings_repository,
            task_repository,
        })
    }

    /// Создаёт экземпляр без Tokio runtime
    ///
    /// Используется в Dioxus приложении, которое не может блокировать
    /// на async операциях инициализации.
    pub fn init_sync(db_path: &str) -> Result<Self, ServicesInitError> {
        let rt = tokio::runtime::Runtime::new()
            .map_err(|e| ServicesInitError::Database(e.to_string()))?;

        rt.block_on(Self::init(db_path))
    }
}
