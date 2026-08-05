//! Репозиторий для работы с сессиями (window и idle)

use super::super::models::{
    AppStatistics, IdleSession, NewIdleSession, NewWindowSession, WindowSession,
};
use chrono::{DateTime, NaiveDate, NaiveTime, TimeZone, Utc};
use chrono_tz::Tz;
use sqlx::SqlitePool;
use thiserror::Error;

/// Ошибки репозитория сессий
#[derive(Debug, Error)]
pub enum SessionRepositoryError {
    #[error("Ошибка базы данных: {0}")]
    Database(#[from] sqlx::Error),

    #[error("Сессия не найдена")]
    NotFound,
}

/// Репозиторий сессий
pub struct SessionRepository {
    pool: SqlitePool,
}

impl SessionRepository {
    /// Создаёт новый репозиторий
    pub fn new(pool: SqlitePool) -> Self {
        Self { pool }
    }

    /// Создаёт сессию окна
    pub async fn create_window(
        &self,
        session: NewWindowSession,
    ) -> Result<WindowSession, SessionRepositoryError> {
        let result = sqlx::query(
            r#"
            INSERT INTO window_session (
                start_ts, end_ts, duration,
                executable_name, executable_path, window_title
            )
            VALUES (?, ?, ?, ?, ?, ?)
            "#,
        )
        .bind(session.start_ts)
        .bind(session.end_ts)
        .bind(session.duration)
        .bind(&session.executable_name)
        .bind(&session.executable_path)
        .bind(&session.window_title)
        .execute(&self.pool)
        .await?;

        let id = result.last_insert_rowid();
        self.get_window_by_id(id).await
    }

    /// Получает сессию окна по ID
    pub async fn get_window_by_id(&self, id: i64) -> Result<WindowSession, SessionRepositoryError> {
        let session = sqlx::query_as::<_, WindowSession>(
            "SELECT id, start_ts, end_ts, duration, executable_name, executable_path, window_title FROM window_session WHERE id = ?"
        )
        .bind(id)
        .fetch_optional(&self.pool)
        .await?
        .ok_or(SessionRepositoryError::NotFound)?;

        Ok(session)
    }

    /// Обновляет сессию окна (завершает её)
    pub async fn update_window(
        &self,
        id: i64,
        end_ts: DateTime<Utc>,
        duration: i64,
    ) -> Result<WindowSession, SessionRepositoryError> {
        sqlx::query("UPDATE window_session SET end_ts = ?, duration = ? WHERE id = ?")
            .bind(end_ts)
            .bind(duration)
            .bind(id)
            .execute(&self.pool)
            .await?;

        self.get_window_by_id(id).await
    }

    /// Создаёт сессию бездействия
    pub async fn create_idle(
        &self,
        session: NewIdleSession,
    ) -> Result<IdleSession, SessionRepositoryError> {
        let result = sqlx::query(
            r#"
            INSERT INTO idle_session (start_ts, end_ts, duration)
            VALUES (?, ?, ?)
            "#,
        )
        .bind(session.start_ts)
        .bind(session.end_ts)
        .bind(session.duration)
        .execute(&self.pool)
        .await?;

        let id = result.last_insert_rowid();
        self.get_idle_by_id(id).await
    }

    /// Получает сессию бездействия по ID
    pub async fn get_idle_by_id(&self, id: i64) -> Result<IdleSession, SessionRepositoryError> {
        let session = sqlx::query_as::<_, IdleSession>(
            "SELECT id, start_ts, end_ts, duration FROM idle_session WHERE id = ?",
        )
        .bind(id)
        .fetch_optional(&self.pool)
        .await?
        .ok_or(SessionRepositoryError::NotFound)?;

        Ok(session)
    }

    /// Обновляет сессию бездействия
    pub async fn update_idle(
        &self,
        id: i64,
        end_ts: DateTime<Utc>,
        duration: i64,
    ) -> Result<IdleSession, SessionRepositoryError> {
        sqlx::query("UPDATE idle_session SET end_ts = ?, duration = ? WHERE id = ?")
            .bind(end_ts)
            .bind(duration)
            .bind(id)
            .execute(&self.pool)
            .await?;

        self.get_idle_by_id(id).await
    }

    /// Получает сессии по дате (в локальном часовом поясе)
    pub async fn get_window_sessions_by_date(
        &self,
        date: NaiveDate,
        client_tz: Tz,
    ) -> Result<Vec<WindowSession>, SessionRepositoryError> {
        // Конвертируем дату в диапазон UTC
        let start_of_day = client_tz
            .from_local_datetime(&date.and_time(NaiveTime::from_hms_opt(0, 0, 0).unwrap()))
            .earliest()
            .unwrap()
            .with_timezone(&Utc);

        let end_of_day = client_tz
            .from_local_datetime(
                &date.and_time(NaiveTime::from_hms_milli_opt(23, 59, 59, 999).unwrap()),
            )
            .latest()
            .unwrap()
            .with_timezone(&Utc);

        let sessions = sqlx::query_as::<_, WindowSession>(
            r#"
            SELECT id, start_ts, end_ts, duration, executable_name, executable_path, window_title
            FROM window_session
            WHERE start_ts >= ? AND start_ts <= ?
            ORDER BY start_ts DESC
            "#,
        )
        .bind(start_of_day)
        .bind(end_of_day)
        .fetch_all(&self.pool)
        .await?;

        Ok(sessions)
    }

    /// Агрегирует статистику по приложениям за день
    pub async fn aggregate_statistics(
        &self,
        date: NaiveDate,
        _client_tz: Tz,
    ) -> Result<Vec<AppStatistics>, SessionRepositoryError> {
        // Формируем строку даты в формате YYYY-MM-DD
        let date_str = date.format("%Y-%m-%d").to_string();

        let stats = sqlx::query_as::<_, (String, i64, i64)>(
            r#"
            SELECT 
                executable_name,
                SUM(duration) as total_duration,
                COUNT(*) as session_count
            FROM window_session
            WHERE DATE(start_ts, 'localtime') = ?
              AND end_ts IS NOT NULL
            GROUP BY executable_name
            ORDER BY total_duration DESC
            "#,
        )
        .bind(&date_str)
        .fetch_all(&self.pool)
        .await?
        .into_iter()
        .map(
            |(executable_name, total_duration, session_count)| AppStatistics {
                executable_name,
                total_duration,
                session_count,
            },
        )
        .collect();

        Ok(stats)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::Duration;

    async fn create_test_pool() -> SqlitePool {
        sqlx::SqlitePool::connect(":memory:").await.unwrap()
    }

    async fn setup_test_data(pool: &SqlitePool) {
        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS window_session (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_ts DATETIME NOT NULL,
                end_ts DATETIME,
                duration INTEGER NOT NULL,
                executable_name VARCHAR(255) NOT NULL,
                executable_path VARCHAR(255),
                window_title VARCHAR(255)
            );

            CREATE TABLE IF NOT EXISTS idle_session (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_ts DATETIME NOT NULL,
                end_ts DATETIME,
                duration INTEGER NOT NULL
            );
            "#,
        )
        .execute(pool)
        .await
        .unwrap();
    }

    #[tokio::test]
    async fn test_window_session_crud() {
        let pool = create_test_pool().await;
        setup_test_data(&pool).await;

        let repo = SessionRepository::new(pool.clone());

        // Create
        let start_ts = Utc::now();
        let new_session = NewWindowSession {
            start_ts,
            end_ts: None,
            duration: 0,
            executable_name: "code".to_string(),
            executable_path: Some("/usr/bin/code".to_string()),
            window_title: Some("TimeTracker - VS Code".to_string()),
        };
        let created = repo.create_window(new_session).await.unwrap();
        assert!(created.id.is_some());
        assert_eq!(created.executable_name, "code");

        // Update (завершаем сессию)
        let end_ts = start_ts + Duration::seconds(300);
        let updated = repo
            .update_window(created.id.unwrap(), end_ts, 300)
            .await
            .unwrap();
        assert!(updated.end_ts.is_some());
        assert_eq!(updated.duration, 300);

        // Read
        let found = repo.get_window_by_id(created.id.unwrap()).await.unwrap();
        assert_eq!(found.executable_name, "code");
    }

    #[tokio::test]
    async fn test_idle_session_crud() {
        let pool = create_test_pool().await;
        setup_test_data(&pool).await;

        let repo = SessionRepository::new(pool.clone());

        // Create
        let start_ts = Utc::now();
        let new_session = NewIdleSession {
            start_ts,
            end_ts: None,
            duration: 0,
        };
        let created = repo.create_idle(new_session).await.unwrap();
        assert!(created.id.is_some());

        // Update
        let end_ts = start_ts + Duration::seconds(60);
        let updated = repo
            .update_idle(created.id.unwrap(), end_ts, 60)
            .await
            .unwrap();
        assert_eq!(updated.duration, 60);
    }

    #[tokio::test]
    async fn test_bug_b3_duration_25_hours() {
        let pool = create_test_pool().await;
        setup_test_data(&pool).await;

        let repo = SessionRepository::new(pool.clone());

        // Сессия 25 часов
        let start_ts = Utc::now() - Duration::hours(25);
        let end_ts = Utc::now();

        // **Исправление бага B3**: используем num_seconds() вместо .seconds
        let duration = (end_ts - start_ts).num_seconds();
        assert_eq!(duration, 90_000); // 25 * 3600 = 90 000 секунд

        let new_session = NewWindowSession {
            start_ts,
            end_ts: Some(end_ts),
            duration,
            executable_name: "long_session".to_string(),
            executable_path: None,
            window_title: None,
        };
        let created = repo.create_window(new_session).await.unwrap();
        assert_eq!(created.duration, 90_000);
    }

    #[tokio::test]
    async fn test_bug_b3_negative_delta() {
        let pool = create_test_pool().await;
        setup_test_data(&pool).await;

        let repo = SessionRepository::new(pool.clone());

        // Отрицательная дельта (start_ts > end_ts)
        let start_ts = Utc::now();
        let end_ts = Utc::now() - Duration::hours(1);

        // **Исправление бага B3**: проверяем на отрицательную дельту
        let delta = end_ts - start_ts;
        let duration = if delta.num_seconds() > 0 {
            delta.num_seconds()
        } else {
            0
        };
        assert_eq!(duration, 0);

        let new_session = NewWindowSession {
            start_ts,
            end_ts: Some(end_ts),
            duration,
            executable_name: "negative_delta".to_string(),
            executable_path: None,
            window_title: None,
        };
        let created = repo.create_window(new_session).await.unwrap();
        assert_eq!(created.duration, 0);
    }

    #[tokio::test]
    async fn test_aggregate_statistics() {
        let pool = create_test_pool().await;
        setup_test_data(&pool).await;

        let repo = SessionRepository::new(pool.clone());
        let tz: Tz = "Europe/Moscow".parse().unwrap();

        // Создаём несколько сессий
        let now = Utc::now();

        repo.create_window(NewWindowSession {
            start_ts: now,
            end_ts: Some(now + Duration::seconds(300)),
            duration: 300,
            executable_name: "code".to_string(),
            executable_path: None,
            window_title: None,
        })
        .await
        .unwrap();

        repo.create_window(NewWindowSession {
            start_ts: now,
            end_ts: Some(now + Duration::seconds(200)),
            duration: 200,
            executable_name: "code".to_string(),
            executable_path: None,
            window_title: None,
        })
        .await
        .unwrap();

        repo.create_window(NewWindowSession {
            start_ts: now,
            end_ts: Some(now + Duration::seconds(150)),
            duration: 150,
            executable_name: "browser".to_string(),
            executable_path: None,
            window_title: None,
        })
        .await
        .unwrap();

        // Получаем статистику
        let stats = repo
            .aggregate_statistics(now.date_naive(), tz)
            .await
            .unwrap();

        // code: 500 секунд, 2 сессии
        // browser: 150 секунд, 1 сессия
        assert_eq!(stats.len(), 2);
        assert_eq!(stats[0].executable_name, "code");
        assert_eq!(stats[0].total_duration, 500);
        assert_eq!(stats[0].session_count, 2);
        assert_eq!(stats[1].executable_name, "browser");
        assert_eq!(stats[1].total_duration, 150);
        assert_eq!(stats[1].session_count, 1);
    }
}
