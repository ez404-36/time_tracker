//! Репозиторий для работы с настройками (singleton)

use super::super::models::{
    NewSettings, NewSettingsAudioParam, Settings, SettingsAudioParam, UpdateSettings,
    UpdateSettingsAudioParam,
};
use serde_json::json;
use sqlx::SqlitePool;
use thiserror::Error;

/// Ошибки репозитория настроек
#[derive(Debug, Error)]
pub enum SettingsRepositoryError {
    #[error("Ошибка базы данных: {0}")]
    Database(#[from] sqlx::Error),

    #[error("Настройки не найдены")]
    NotFound,
}

/// Репозиторий настроек (singleton pattern)
pub struct SettingsRepository {
    pool: SqlitePool,
}

impl SettingsRepository {
    /// Создаёт новый репозиторий
    pub fn new(pool: SqlitePool) -> Self {
        Self { pool }
    }

    /// Получает или создаёт настройки (singleton)
    pub async fn get_or_create(&self) -> Result<Settings, SettingsRepositoryError> {
        // Пытаемся получить существующие настройки
        let existing = sqlx::query_as::<_, Settings>(
            r#"
            SELECT 
                id, client_timezone, idle_threshold,
                enable_window_tracking, enable_idle_tracking, enable_pomodoro,
                pomodoro_work_time, pomodoro_rest_time, ui_settings,
                task_deadline_sound_config_id, idle_sound_config_id, pomodoro_sound_config_id,
                autostart_enabled, start_minimized, close_to_tray, autostart_tracking
            FROM settings
            LIMIT 1
            "#,
        )
        .fetch_optional(&self.pool)
        .await?;

        if let Some(settings) = existing {
            return Ok(settings);
        }

        // Создаём настройки по умолчанию
        let default = NewSettings {
            client_timezone: "Europe/Moscow".to_string(),
            idle_threshold: 60,
            enable_window_tracking: false,
            enable_idle_tracking: false,
            enable_pomodoro: false,
            pomodoro_work_time: None,
            pomodoro_rest_time: None,
            ui_settings: json!({}),
            task_deadline_sound_config_id: None,
            idle_sound_config_id: None,
            pomodoro_sound_config_id: None,
            autostart_enabled: false,
            start_minimized: false,
            close_to_tray: false,
            autostart_tracking: false,
        };

        let result = sqlx::query(
            r#"
            INSERT INTO settings (
                client_timezone, idle_threshold,
                enable_window_tracking, enable_idle_tracking, enable_pomodoro,
                pomodoro_work_time, pomodoro_rest_time, ui_settings,
                task_deadline_sound_config_id, idle_sound_config_id, pomodoro_sound_config_id,
                autostart_enabled, start_minimized, close_to_tray, autostart_tracking
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            "#,
        )
        .bind(&default.client_timezone)
        .bind(default.idle_threshold)
        .bind(default.enable_window_tracking)
        .bind(default.enable_idle_tracking)
        .bind(default.enable_pomodoro)
        .bind(default.pomodoro_work_time)
        .bind(default.pomodoro_rest_time)
        .bind(&default.ui_settings)
        .bind(default.task_deadline_sound_config_id)
        .bind(default.idle_sound_config_id)
        .bind(default.pomodoro_sound_config_id)
        .bind(default.autostart_enabled)
        .bind(default.start_minimized)
        .bind(default.close_to_tray)
        .bind(default.autostart_tracking)
        .execute(&self.pool)
        .await?;

        let id = result.last_insert_rowid();
        self.get_by_id(id).await
    }

    /// Получает настройки по ID
    pub async fn get_by_id(&self, id: i64) -> Result<Settings, SettingsRepositoryError> {
        let settings = sqlx::query_as::<_, Settings>(
            r#"
            SELECT 
                id, client_timezone, idle_threshold,
                enable_window_tracking, enable_idle_tracking, enable_pomodoro,
                pomodoro_work_time, pomodoro_rest_time, ui_settings,
                task_deadline_sound_config_id, idle_sound_config_id, pomodoro_sound_config_id,
                autostart_enabled, start_minimized, close_to_tray, autostart_tracking
            FROM settings
            WHERE id = ?
            "#,
        )
        .bind(id)
        .fetch_optional(&self.pool)
        .await?
        .ok_or(SettingsRepositoryError::NotFound)?;

        Ok(settings)
    }

    /// Обновляет настройки
    pub async fn update(
        &self,
        id: i64,
        update: UpdateSettings,
    ) -> Result<Settings, SettingsRepositoryError> {
        let mut query = String::from("UPDATE settings SET ");
        let mut first = true;
        let mut bind_order: Vec<String> = Vec::new();

        if update.client_timezone.is_some() {
            if !first {
                query.push_str(", ");
            }
            query.push_str("client_timezone = ?");
            bind_order.push("client_timezone".to_string());
            first = false;
        }
        if update.idle_threshold.is_some() {
            if !first {
                query.push_str(", ");
            }
            query.push_str("idle_threshold = ?");
            bind_order.push("idle_threshold".to_string());
            first = false;
        }
        if update.enable_window_tracking.is_some() {
            if !first {
                query.push_str(", ");
            }
            query.push_str("enable_window_tracking = ?");
            bind_order.push("enable_window_tracking".to_string());
            first = false;
        }
        if update.enable_idle_tracking.is_some() {
            if !first {
                query.push_str(", ");
            }
            query.push_str("enable_idle_tracking = ?");
            bind_order.push("enable_idle_tracking".to_string());
            first = false;
        }
        if update.enable_pomodoro.is_some() {
            if !first {
                query.push_str(", ");
            }
            query.push_str("enable_pomodoro = ?");
            bind_order.push("enable_pomodoro".to_string());
            first = false;
        }
        if update.pomodoro_work_time.is_some() {
            if !first {
                query.push_str(", ");
            }
            query.push_str("pomodoro_work_time = ?");
            bind_order.push("pomodoro_work_time".to_string());
            first = false;
        }
        if update.pomodoro_rest_time.is_some() {
            if !first {
                query.push_str(", ");
            }
            query.push_str("pomodoro_rest_time = ?");
            bind_order.push("pomodoro_rest_time".to_string());
            first = false;
        }
        if update.ui_settings.is_some() {
            if !first {
                query.push_str(", ");
            }
            query.push_str("ui_settings = ?");
            bind_order.push("ui_settings".to_string());
            first = false;
        }
        if update.task_deadline_sound_config_id.is_some() {
            if !first {
                query.push_str(", ");
            }
            query.push_str("task_deadline_sound_config_id = ?");
            bind_order.push("task_deadline_sound_config_id".to_string());
            first = false;
        }
        if update.idle_sound_config_id.is_some() {
            if !first {
                query.push_str(", ");
            }
            query.push_str("idle_sound_config_id = ?");
            bind_order.push("idle_sound_config_id".to_string());
            first = false;
        }
        if update.pomodoro_sound_config_id.is_some() {
            if !first {
                query.push_str(", ");
            }
            query.push_str("pomodoro_sound_config_id = ?");
            bind_order.push("pomodoro_sound_config_id".to_string());
            first = false;
        }
        if update.autostart_enabled.is_some() {
            if !first {
                query.push_str(", ");
            }
            query.push_str("autostart_enabled = ?");
            bind_order.push("autostart_enabled".to_string());
            first = false;
        }
        if update.start_minimized.is_some() {
            if !first {
                query.push_str(", ");
            }
            query.push_str("start_minimized = ?");
            bind_order.push("start_minimized".to_string());
            first = false;
        }
        if update.close_to_tray.is_some() {
            if !first {
                query.push_str(", ");
            }
            query.push_str("close_to_tray = ?");
            bind_order.push("close_to_tray".to_string());
            first = false;
        }
        if update.autostart_tracking.is_some() {
            if !first {
                query.push_str(", ");
            }
            query.push_str("autostart_tracking = ?");
            bind_order.push("autostart_tracking".to_string());
            first = false;
        }

        if first {
            return self.get_by_id(id).await;
        }

        query.push_str(" WHERE id = ?");

        let mut q = sqlx::query(&query);

        for field in &bind_order {
            match field.as_str() {
                "client_timezone" => q = q.bind(update.client_timezone.as_ref().unwrap()),
                "idle_threshold" => q = q.bind(update.idle_threshold.unwrap()),
                "enable_window_tracking" => q = q.bind(update.enable_window_tracking.unwrap()),
                "enable_idle_tracking" => q = q.bind(update.enable_idle_tracking.unwrap()),
                "enable_pomodoro" => q = q.bind(update.enable_pomodoro.unwrap()),
                "pomodoro_work_time" => q = q.bind(update.pomodoro_work_time.as_ref().unwrap()),
                "pomodoro_rest_time" => q = q.bind(update.pomodoro_rest_time.as_ref().unwrap()),
                "ui_settings" => q = q.bind(update.ui_settings.as_ref().unwrap()),
                "task_deadline_sound_config_id" => {
                    q = q.bind(update.task_deadline_sound_config_id.as_ref().unwrap())
                }
                "idle_sound_config_id" => q = q.bind(update.idle_sound_config_id.as_ref().unwrap()),
                "pomodoro_sound_config_id" => {
                    q = q.bind(update.pomodoro_sound_config_id.as_ref().unwrap())
                }
                "autostart_enabled" => q = q.bind(update.autostart_enabled.unwrap()),
                "start_minimized" => q = q.bind(update.start_minimized.unwrap()),
                "close_to_tray" => q = q.bind(update.close_to_tray.unwrap()),
                "autostart_tracking" => q = q.bind(update.autostart_tracking.unwrap()),
                _ => {}
            }
        }

        q = q.bind(id);
        q.execute(&self.pool).await?;

        self.get_by_id(id).await
    }

    /// Обновляет только UI-настройки (JSON)
    pub async fn update_ui_settings(
        &self,
        id: i64,
        ui_settings: serde_json::Value,
    ) -> Result<Settings, SettingsRepositoryError> {
        sqlx::query("UPDATE settings SET ui_settings = ? WHERE id = ?")
            .bind(&ui_settings)
            .bind(id)
            .execute(&self.pool)
            .await?;

        self.get_by_id(id).await
    }

    /// Создаёт параметры звукового уведомления
    pub async fn create_audio_param(
        &self,
        param: NewSettingsAudioParam,
    ) -> Result<SettingsAudioParam, SettingsRepositoryError> {
        let result = sqlx::query(
            "INSERT INTO settings_audio_param (disabled, sound, volume_offset) VALUES (?, ?, ?)",
        )
        .bind(param.disabled)
        .bind(&param.sound)
        .bind(param.volume_offset)
        .execute(&self.pool)
        .await?;

        let id = result.last_insert_rowid();
        self.get_audio_param_by_id(id).await
    }

    /// Получает параметры звука по ID
    pub async fn get_audio_param_by_id(
        &self,
        id: i64,
    ) -> Result<SettingsAudioParam, SettingsRepositoryError> {
        let param = sqlx::query_as::<_, SettingsAudioParam>(
            "SELECT id, disabled, sound, volume_offset FROM settings_audio_param WHERE id = ?",
        )
        .bind(id)
        .fetch_optional(&self.pool)
        .await?
        .ok_or(SettingsRepositoryError::NotFound)?;

        Ok(param)
    }

    /// Обновляет параметры звука
    pub async fn update_audio_param(
        &self,
        id: i64,
        update: UpdateSettingsAudioParam,
    ) -> Result<SettingsAudioParam, SettingsRepositoryError> {
        let mut query = String::from("UPDATE settings_audio_param SET ");
        let mut first = true;
        let mut bind_order: Vec<String> = Vec::new();

        if update.disabled.is_some() {
            if !first {
                query.push_str(", ");
            }
            query.push_str("disabled = ?");
            bind_order.push("disabled".to_string());
            first = false;
        }
        if update.sound.is_some() {
            if !first {
                query.push_str(", ");
            }
            query.push_str("sound = ?");
            bind_order.push("sound".to_string());
            first = false;
        }
        if update.volume_offset.is_some() {
            if !first {
                query.push_str(", ");
            }
            query.push_str("volume_offset = ?");
            bind_order.push("volume_offset".to_string());
            first = false;
        }

        if first {
            return self.get_audio_param_by_id(id).await;
        }

        query.push_str(" WHERE id = ?");

        let mut q = sqlx::query(&query);

        if let Some(disabled) = update.disabled {
            q = q.bind(disabled);
        }
        if let Some(sound) = &update.sound {
            q = q.bind(sound);
        }
        if let Some(volume_offset) = update.volume_offset {
            q = q.bind(volume_offset);
        }

        q = q.bind(id);
        q.execute(&self.pool).await?;

        self.get_audio_param_by_id(id).await
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    async fn create_test_pool() -> SqlitePool {
        sqlx::SqlitePool::connect(":memory:").await.unwrap()
    }

    async fn setup_test_data(pool: &SqlitePool) {
        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_timezone VARCHAR(255) NOT NULL DEFAULT 'Europe/Moscow',
                idle_threshold INTEGER NOT NULL DEFAULT 60,
                enable_window_tracking BOOLEAN NOT NULL DEFAULT 0,
                enable_idle_tracking BOOLEAN NOT NULL DEFAULT 0,
                enable_pomodoro BOOLEAN NOT NULL DEFAULT 0,
                pomodoro_work_time SMALLINT,
                pomodoro_rest_time SMALLINT,
                ui_settings JSON NOT NULL DEFAULT '{}',
                task_deadline_sound_config_id INTEGER,
                idle_sound_config_id INTEGER,
                pomodoro_sound_config_id INTEGER,
                autostart_enabled BOOLEAN NOT NULL DEFAULT 0,
                start_minimized BOOLEAN NOT NULL DEFAULT 0,
                close_to_tray BOOLEAN NOT NULL DEFAULT 0,
                autostart_tracking BOOLEAN NOT NULL DEFAULT 0,
                FOREIGN KEY (task_deadline_sound_config_id) REFERENCES settings_audio_param(id) ON DELETE SET NULL,
                FOREIGN KEY (idle_sound_config_id) REFERENCES settings_audio_param(id) ON DELETE SET NULL,
                FOREIGN KEY (pomodoro_sound_config_id) REFERENCES settings_audio_param(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS settings_audio_param (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                disabled BOOLEAN NOT NULL DEFAULT 0,
                sound VARCHAR(255),
                volume_offset DECIMAL(3,1) NOT NULL DEFAULT 0.0
            );
            "#
        )
        .execute(pool)
        .await
        .unwrap();
    }

    #[tokio::test]
    async fn test_settings_singleton() {
        let pool = create_test_pool().await;
        setup_test_data(&pool).await;

        let repo = SettingsRepository::new(pool.clone());

        // Первый вызов - создаёт настройки
        let settings1 = repo.get_or_create().await.unwrap();
        assert_eq!(settings1.client_timezone, "Europe/Moscow");
        assert_eq!(settings1.idle_threshold, 60);

        // Второй вызов - возвращает те же настройки
        let settings2 = repo.get_or_create().await.unwrap();
        assert_eq!(settings1.id, settings2.id);

        // Обновляем настройки
        let update = UpdateSettings {
            client_timezone: Some("America/New_York".to_string()),
            idle_threshold: Some(120),
            ..Default::default()
        };
        let updated = repo.update(settings1.id.unwrap(), update).await.unwrap();
        assert_eq!(updated.client_timezone, "America/New_York");
        assert_eq!(updated.idle_threshold, 120);
    }

    #[tokio::test]
    async fn test_update_ui_settings() {
        let pool = create_test_pool().await;
        setup_test_data(&pool).await;

        let repo = SettingsRepository::new(pool.clone());

        let settings = repo.get_or_create().await.unwrap();

        let new_ui = json!({
            "theme": "dark",
            "window_width": 1200,
            "window_height": 800
        });

        let updated = repo
            .update_ui_settings(settings.id.unwrap(), new_ui.clone())
            .await
            .unwrap();
        assert_eq!(updated.ui_settings, new_ui);
    }

    #[tokio::test]
    async fn test_audio_param_crud() {
        let pool = create_test_pool().await;
        setup_test_data(&pool).await;

        let repo = SettingsRepository::new(pool.clone());

        // Create
        let new_param = NewSettingsAudioParam {
            disabled: false,
            sound: Some("notification.mp3".to_string()),
            volume_offset: 0.5,
        };
        let created = repo.create_audio_param(new_param).await.unwrap();
        assert!(created.id.is_some());
        assert_eq!(created.sound, Some("notification.mp3".to_string()));

        // Read
        let found = repo
            .get_audio_param_by_id(created.id.unwrap())
            .await
            .unwrap();
        assert_eq!(found.volume_offset, 0.5);

        // Update
        let update = UpdateSettingsAudioParam {
            volume_offset: Some(0.8),
            ..Default::default()
        };
        let updated = repo
            .update_audio_param(created.id.unwrap(), update)
            .await
            .unwrap();
        assert_eq!(updated.volume_offset, 0.8);
    }
}
