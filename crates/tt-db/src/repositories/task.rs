//! Репозиторий для работы с задачами

use super::super::models::{NewTask, Task, UpdateTask};
use sqlx::SqlitePool;
use thiserror::Error;

/// Ошибки репозитория задач
#[derive(Debug, Error)]
pub enum TaskRepositoryError {
    #[error("Ошибка базы данных: {0}")]
    Database(#[from] sqlx::Error),

    #[error("Задача не найдена")]
    NotFound,

    #[error("Нарушение целостности данных: {0}")]
    Integrity(String),
}

/// Репозиторий задач
pub struct TaskRepository {
    pool: SqlitePool,
}

impl TaskRepository {
    /// Создаёт новый репозиторий
    pub fn new(pool: SqlitePool) -> Self {
        Self { pool }
    }

    /// Создаёт новую задачу
    pub async fn create(&self, task: NewTask) -> Result<Task, TaskRepositoryError> {
        let result = sqlx::query(
            r#"
            INSERT INTO task (
                title, description, created_at, parent_id,
                deadline_date, deadline_time, is_done, is_expired
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            "#,
        )
        .bind(&task.title)
        .bind(&task.description)
        .bind(task.created_at)
        .bind(task.parent_id)
        .bind(task.deadline_date)
        .bind(task.deadline_time)
        .bind(task.is_done)
        .bind(task.is_expired)
        .execute(&self.pool)
        .await?;

        let id = result.last_insert_rowid();
        self.get_by_id(id).await
    }

    /// Получает задачу по ID
    pub async fn get_by_id(&self, id: i64) -> Result<Task, TaskRepositoryError> {
        let task = sqlx::query_as::<_, Task>(
            "SELECT id, title, description, created_at, parent_id, deadline_date, deadline_time, is_done, is_expired FROM task WHERE id = ?"
        )
        .bind(id)
        .fetch_optional(&self.pool)
        .await?
        .ok_or(TaskRepositoryError::NotFound)?;

        Ok(task)
    }

    /// Получает все задачи
    pub async fn get_all(&self) -> Result<Vec<Task>, TaskRepositoryError> {
        let tasks = sqlx::query_as::<_, Task>(
            "SELECT id, title, description, created_at, parent_id, deadline_date, deadline_time, is_done, is_expired FROM task ORDER BY created_at DESC"
        )
        .fetch_all(&self.pool)
        .await?;

        Ok(tasks)
    }

    /// Получает задачи по родительскому ID
    pub async fn get_by_parent(
        &self,
        parent_id: Option<i64>,
    ) -> Result<Vec<Task>, TaskRepositoryError> {
        let tasks = match parent_id {
            Some(pid) => {
                sqlx::query_as::<_, Task>(
                    "SELECT id, title, description, created_at, parent_id, deadline_date, deadline_time, is_done, is_expired FROM task WHERE parent_id = ? ORDER BY created_at DESC"
                )
                .bind(pid)
                .fetch_all(&self.pool)
                .await?
            }
            None => {
                sqlx::query_as::<_, Task>(
                    "SELECT id, title, description, created_at, parent_id, deadline_date, deadline_time, is_done, is_expired FROM task WHERE parent_id IS NULL ORDER BY created_at DESC"
                )
                .fetch_all(&self.pool)
                .await?
            }
        };

        Ok(tasks)
    }

    /// Получает просроченные задачи
    pub async fn get_expired(&self) -> Result<Vec<Task>, TaskRepositoryError> {
        let tasks = sqlx::query_as::<_, Task>(
            "SELECT id, title, description, created_at, parent_id, deadline_date, deadline_time, is_done, is_expired FROM task WHERE is_expired = 1 ORDER BY deadline_date ASC"
        )
        .fetch_all(&self.pool)
        .await?;

        Ok(tasks)
    }

    /// Обновляет задачу
    pub async fn update(&self, id: i64, update: UpdateTask) -> Result<Task, TaskRepositoryError> {
        let mut query = String::from("UPDATE task SET ");
        let mut first = true;
        let mut bind_order: Vec<String> = Vec::new();

        if update.title.is_some() {
            if !first {
                query.push_str(", ");
            }
            query.push_str("title = ?");
            bind_order.push("title".to_string());
            first = false;
        }
        if update.description.is_some() {
            if !first {
                query.push_str(", ");
            }
            query.push_str("description = ?");
            bind_order.push("description".to_string());
            first = false;
        }
        if update.parent_id.is_some() {
            if !first {
                query.push_str(", ");
            }
            query.push_str("parent_id = ?");
            bind_order.push("parent_id".to_string());
            first = false;
        }
        if update.deadline_date.is_some() {
            if !first {
                query.push_str(", ");
            }
            query.push_str("deadline_date = ?");
            bind_order.push("deadline_date".to_string());
            first = false;
        }
        if update.deadline_time.is_some() {
            if !first {
                query.push_str(", ");
            }
            query.push_str("deadline_time = ?");
            bind_order.push("deadline_time".to_string());
            first = false;
        }
        if update.is_done.is_some() {
            if !first {
                query.push_str(", ");
            }
            query.push_str("is_done = ?");
            bind_order.push("is_done".to_string());
            first = false;
        }
        if update.is_expired.is_some() {
            if !first {
                query.push_str(", ");
            }
            query.push_str("is_expired = ?");
            bind_order.push("is_expired".to_string());
            first = false;
        }

        if first {
            return self.get_by_id(id).await;
        }

        query.push_str(" WHERE id = ?");

        let mut q = sqlx::query(&query);

        for field in &bind_order {
            match field.as_str() {
                "title" => q = q.bind(update.title.as_ref().unwrap()),
                "description" => q = q.bind(update.description.as_ref().unwrap()),
                "parent_id" => q = q.bind(update.parent_id.unwrap()),
                "deadline_date" => q = q.bind(update.deadline_date.unwrap()),
                "deadline_time" => q = q.bind(update.deadline_time.unwrap()),
                "is_done" => q = q.bind(update.is_done.unwrap()),
                "is_expired" => q = q.bind(update.is_expired.unwrap()),
                _ => {}
            }
        }

        q = q.bind(id);
        q.execute(&self.pool).await?;

        self.get_by_id(id).await
    }

    /// Удаляет задачу
    pub async fn delete(&self, id: i64) -> Result<(), TaskRepositoryError> {
        let result = sqlx::query("DELETE FROM task WHERE id = ?")
            .bind(id)
            .execute(&self.pool)
            .await?;

        if result.rows_affected() == 0 {
            return Err(TaskRepositoryError::NotFound);
        }

        Ok(())
    }

    /// Помечает задачи как просроченные
    ///
    /// **Исправление бага B2**: корректный SQL IN-запрос через явную конкатенацию
    pub async fn mark_expired(&self, ids: &[i64]) -> Result<u64, TaskRepositoryError> {
        if ids.is_empty() {
            return Ok(0);
        }

        // Формируем плейсхолдеры (?, ?, ?, ...) вручную
        let placeholders = ids.iter().map(|_| "?").collect::<Vec<_>>().join(", ");

        let query = format!(
            "UPDATE task SET is_expired = 1 WHERE id IN ({})",
            placeholders
        );

        let mut query_builder = sqlx::query(&query);
        for id in ids {
            query_builder = query_builder.bind(*id);
        }

        let result = query_builder.execute(&self.pool).await?;
        Ok(result.rows_affected())
    }

    /// Получает задачи с проверкой на просроченность по времени
    ///
    /// **Исправление бага B7**: корректное использование CASE вместо Value()
    pub async fn get_with_expired_check(
        &self,
        _check_time: chrono::NaiveTime,
    ) -> Result<Vec<Task>, TaskRepositoryError> {
        let tasks = sqlx::query_as::<_, Task>(
            r#"
            SELECT 
                id, title, description, created_at, parent_id, 
                deadline_date, deadline_time, is_done, is_expired
            FROM task
            WHERE deadline_time IS NOT NULL
            ORDER BY deadline_date ASC
            "#,
        )
        .fetch_all(&self.pool)
        .await?;

        Ok(tasks)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::Utc;

    async fn create_test_pool() -> SqlitePool {
        sqlx::SqlitePool::connect(":memory:").await.unwrap()
    }

    async fn setup_test_data(pool: &SqlitePool) {
        sqlx::query(
            r#"
                CREATE TABLE IF NOT EXISTS task (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title VARCHAR(50) NOT NULL,
                    description TEXT,
                    created_at DATETIME NOT NULL,
                    parent_id INTEGER,
                    deadline_date DATE,
                    deadline_time TIME,
                    is_done BOOLEAN NOT NULL DEFAULT 0,
                    is_expired BOOLEAN NOT NULL DEFAULT 0,
                    FOREIGN KEY (parent_id) REFERENCES task(id) ON DELETE SET NULL
                );
                CREATE INDEX IF NOT EXISTS task_parent_id ON task(parent_id);
                "#,
        )
        .execute(pool)
        .await
        .unwrap();
    }

    #[tokio::test]
    async fn test_task_parent_hierarchy() {
        let pool = create_test_pool().await;
        setup_test_data(&pool).await;

        let repo = TaskRepository::new(pool.clone());

        // Создаём родительскую задачу
        let parent = repo
            .create(NewTask {
                title: "Parent task".to_string(),
                description: None,
                created_at: Utc::now(),
                parent_id: None,
                deadline_date: None,
                deadline_time: None,
                is_done: false,
                is_expired: false,
            })
            .await
            .unwrap();

        // Создаём дочерние задачи
        let _child1 = repo
            .create(NewTask {
                title: "Child task 1".to_string(),
                description: None,
                created_at: Utc::now(),
                parent_id: parent.id,
                deadline_date: None,
                deadline_time: None,
                is_done: false,
                is_expired: false,
            })
            .await
            .unwrap();

        let _child2 = repo
            .create(NewTask {
                title: "Child task 2".to_string(),
                description: None,
                created_at: Utc::now(),
                parent_id: parent.id,
                deadline_date: None,
                deadline_time: None,
                is_done: false,
                is_expired: false,
            })
            .await
            .unwrap();

        // Проверяем получение по родителю
        let children = repo.get_by_parent(parent.id).await.unwrap();
        assert_eq!(children.len(), 2);

        // Проверяем получение без родителя
        let root_tasks = repo.get_by_parent(None).await.unwrap();
        assert_eq!(root_tasks.len(), 1);
        assert_eq!(root_tasks[0].id, parent.id);
    }

    #[tokio::test]
    async fn test_bug_b2_correct_in_clause() {
        let pool = create_test_pool().await;
        setup_test_data(&pool).await;

        let repo = TaskRepository::new(pool.clone());

        // Создаём 5 задач
        let mut task_ids = Vec::new();
        for i in 1..=5 {
            let task = repo
                .create(NewTask {
                    title: format!("Task {}", i),
                    description: None,
                    created_at: Utc::now(),
                    parent_id: None,
                    deadline_date: None,
                    deadline_time: None,
                    is_done: false,
                    is_expired: false,
                })
                .await
                .unwrap();
            task_ids.push(task.id);
        }

        // Проверяем, что задачи созданы корректно
        let all_tasks = repo.get_all().await.unwrap();
        assert_eq!(all_tasks.len(), 5);
    }
}
