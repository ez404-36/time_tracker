//! Проверка дедлайнов задач

use chrono::{Timelike, Utc};
use tracing::{debug, info};

use tt_core::EventBus;
use tt_db::{Task, TaskRepository};

/// Проверяльщик дедлайнов задач
///
/// Периодически проверяет задачи с истёкшим дедлайном и публикует события для уведомлений.
///
/// ## Исправление бага B7
///
/// В Python-версии было:
/// ```python
/// Value(Task.deadline_time == _time).alias('is_expired_at_now')
/// ```
///
/// `Value()` оборачивал выражение как литерал-параметр, из-за чего `is_expired_at_now`
/// вычислялось неправильно. В Rust-версии используется корректная логика проверки
/// через прямое сравнение дат и времён.
pub struct DeadlineChecker {
    event_bus: std::sync::Arc<EventBus>,
    task_repository: std::sync::Arc<TaskRepository>,
    check_interval_seconds: u64,
}

impl DeadlineChecker {
    /// Создаёт новый экземпляр проверяльщика дедлайнов
    pub fn new(event_bus: EventBus, task_repository: std::sync::Arc<TaskRepository>) -> Self {
        Self {
            event_bus: std::sync::Arc::new(event_bus),
            task_repository,
            check_interval_seconds: 60, // проверяем каждую минуту
        }
    }

    /// Создаёт тестовый экземпляр проверяльщика дедлайнов (для тестов is_task_expired)
    #[cfg(test)]
    fn new_test(event_bus: EventBus) -> Self {
        // Для тестов is_task_expired репозиторий не нужен,
        // создаём через Tokio runtime для совместимости с sqlx
        let pool = tokio::runtime::Runtime::new()
            .unwrap()
            .block_on(async { sqlx::SqlitePool::connect(":memory:").await })
            .unwrap();

        Self {
            event_bus: std::sync::Arc::new(event_bus),
            task_repository: std::sync::Arc::new(tt_db::TaskRepository::new(pool)),
            check_interval_seconds: 60,
        }
    }

    /// Создаёт тестовый экземпляр проверяльщика дедлайнов для async тестов
    #[cfg(test)]
    async fn new_test_async(event_bus: EventBus) -> Self {
        let pool = sqlx::SqlitePool::connect(":memory:").await.unwrap();

        Self {
            event_bus: std::sync::Arc::new(event_bus),
            task_repository: std::sync::Arc::new(tt_db::TaskRepository::new(pool)),
            check_interval_seconds: 60,
        }
    }

    /// Устанавливает интервал проверки
    pub fn set_check_interval(&mut self, seconds: u64) {
        self.check_interval_seconds = seconds;
    }

    /// Проверяет все задачи на предмет истёкшего дедлайна
    ///
    /// Возвращает список задач, срок которых истёк.
    pub async fn check_deadlines(&self) -> Result<Vec<Task>, Box<dyn std::error::Error>> {
        let now = Utc::now();
        let today = now.date_naive();
        let current_time = now.time();

        debug!(
            "Проверка дедлайнов на {} {:02}:{:02}",
            today,
            current_time.hour(),
            current_time.minute()
        );

        // Получаем все задачи из репозитория
        let all_tasks = self.task_repository.get_all().await?;
        let expired_tasks: Vec<Task> = all_tasks
            .into_iter()
            .filter(|task| {
                if task.is_done || task.is_expired {
                    return false;
                }

                match (task.deadline_date, task.deadline_time) {
                    // Есть и дата, и время — точное сравнение
                    (Some(deadline_date), Some(deadline_time)) => {
                        deadline_date < today
                            || (deadline_date == today && deadline_time <= current_time)
                    }

                    // Есть только дата — считаем истёкшим, если дата прошла
                    (Some(deadline_date), None) => deadline_date < today,

                    // Нет дедлайна — пропускаем
                    (None, _) => false,
                }
            })
            .collect();

        if expired_tasks.is_empty() {
            debug!("Нет задач с истёкшим дедлайном");
        } else {
            info!("Найдено {} задач с истёкшим дедлайном", expired_tasks.len());

            // Публикуем событие для каждой задачи
            for task in &expired_tasks {
                let task_id = task.id.unwrap_or(0);
                let task_title = task.title.clone();

                debug!("Задача истекла: id={}, title={}", task_id, task_title);

                self.event_bus.publish(tt_core::SystemEvent::TasksExpired {
                    task_id,
                    task_title,
                });
            }
        }

        Ok(expired_tasks)
    }

    /// Проверяет конкретную задачу на предмет истёкшего дедлайна
    ///
    /// Возвращает `true`, если дедлайн истёк.
    pub fn is_task_expired(&self, task: &Task) -> bool {
        if task.is_done || task.is_expired {
            return false;
        }

        let now = Utc::now();
        let today = now.date_naive();
        let current_time = now.time();

        match (task.deadline_date, task.deadline_time) {
            (Some(deadline_date), Some(deadline_time)) => {
                deadline_date < today || (deadline_date == today && deadline_time <= current_time)
            }

            (Some(deadline_date), None) => deadline_date < today,

            (None, _) => false,
        }
    }

    /// Основной цикл работы проверяльщика
    ///
    /// Использует `tokio::select!` с `CancellationToken` для мгновенной остановки.
    pub async fn run(
        &self,
        cancellation_token: tokio_util::sync::CancellationToken,
    ) -> Result<(), String> {
        let mut interval =
            tokio::time::interval(std::time::Duration::from_secs(self.check_interval_seconds));

        loop {
            tokio::select! {
                _ = cancellation_token.cancelled() => {
                    debug!("DeadlineChecker получил сигнал отмены");
                    break;
                }
                _ = interval.tick() => {
                    let _ = self.check_deadlines().await;
                }
            }
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::{Duration, NaiveDate, NaiveTime};

    /// Создаёт тестовую задачу
    fn create_test_task(
        id: Option<i64>,
        title: &str,
        deadline_date: Option<NaiveDate>,
        deadline_time: Option<NaiveTime>,
    ) -> Task {
        Task {
            id,
            title: title.to_string(),
            description: None,
            created_at: Utc::now(),
            parent_id: None,
            deadline_date,
            deadline_time,
            is_done: false,
            is_expired: false,
        }
    }

    /// Тест бага B7: дедлайн ровно сейчас
    #[test]
    fn test_b7_deadline_exactly_now() {
        let event_bus = EventBus::new(10);
        let checker = DeadlineChecker::new_test(event_bus);

        let now = Utc::now();
        let today = now.date_naive();
        let current_time = now.time();

        // Задача с дедлайном "ровно сейчас"
        let task = create_test_task(
            Some(1),
            "Task with current deadline",
            Some(today),
            Some(current_time),
        );

        assert!(
            checker.is_task_expired(&task),
            "Задача с дедлайном ровно сейчас должна считаться истёкшей"
        );
    }

    /// Тест бага B7: дедлайн за секунду до
    #[test]
    fn test_b7_deadline_one_second_before() {
        let event_bus = EventBus::new(10);
        let checker = DeadlineChecker::new_test(event_bus);

        let now = Utc::now();
        let today = now.date_naive();
        let one_second_before = now.time() - Duration::seconds(1);

        // Задача с дедлайном на секунду назад
        let task = create_test_task(
            Some(1),
            "Task with past deadline",
            Some(today),
            Some(one_second_before),
        );

        assert!(
            checker.is_task_expired(&task),
            "Задача с дедлайном секунду назад должна считаться истёкшей"
        );
    }

    /// Тест бага B7: дедлайн через секунду после
    #[test]
    fn test_b7_deadline_one_second_after() {
        let event_bus = EventBus::new(10);
        let checker = DeadlineChecker::new_test(event_bus);

        let now = Utc::now();
        let today = now.date_naive();
        let one_second_after = now.time() + Duration::seconds(1);

        // Задача с дедлайном на секунду вперёд
        let task = create_test_task(
            Some(1),
            "Task with future deadline",
            Some(today),
            Some(one_second_after),
        );

        assert!(
            !checker.is_task_expired(&task),
            "Задача с дедлайном секунду вперёд НЕ должна считаться истёкшей"
        );
    }

    /// Тест бага B7: дедлайн отсутствует
    #[test]
    fn test_b7_deadline_none() {
        let event_bus = EventBus::new(10);
        let checker = DeadlineChecker::new_test(event_bus);

        // Задача без дедлайна
        let task = create_test_task(Some(1), "Task without deadline", None, None);

        assert!(
            !checker.is_task_expired(&task),
            "Задача без дедлайна НЕ должна считаться истёкшей"
        );
    }

    /// Тест бага B7: дедлайн только дата (без времени)
    #[test]
    fn test_b7_deadline_date_only() {
        let event_bus = EventBus::new(10);
        let checker = DeadlineChecker::new_test(event_bus);

        let now = Utc::now();
        let today = now.date_naive();
        let yesterday = today - Duration::days(1);
        let tomorrow = today + Duration::days(1);

        // Задача с дедлайном "вчера"
        let task_yesterday =
            create_test_task(Some(1), "Task with past date", Some(yesterday), None);
        assert!(
            checker.is_task_expired(&task_yesterday),
            "Задача с дедлайном вчера должна считаться истёкшей"
        );

        // Задача с дедлайном "сегодня"
        let task_today = create_test_task(Some(2), "Task with today date", Some(today), None);
        assert!(
            !checker.is_task_expired(&task_today),
            "Задача с дедлайном сегодня (без времени) НЕ должна считаться истёкшей"
        );

        // Задача с дедлайном "завтра"
        let task_tomorrow =
            create_test_task(Some(3), "Task with future date", Some(tomorrow), None);
        assert!(
            !checker.is_task_expired(&task_tomorrow),
            "Задача с дедлайном завтра НЕ должна считаться истёкшей"
        );
    }

    /// Тест бага B7: граничные значения времени
    #[test]
    fn test_b7_deadline_time_boundaries() {
        let event_bus = EventBus::new(10);
        let checker = DeadlineChecker::new_test(event_bus);

        let now = Utc::now();
        let today = now.date_naive();
        let current_time = now.time();

        // Граничные значения вокруг текущего времени
        let one_minute_before = current_time - Duration::minutes(1);
        let one_minute_after = current_time + Duration::minutes(1);

        // До — истёк
        let task_before = create_test_task(
            Some(1),
            "Task 1 min before",
            Some(today),
            Some(one_minute_before),
        );
        assert!(
            checker.is_task_expired(&task_before),
            "Задача на минуту до должна считаться истёкшей"
        );

        // После — не истёк
        let task_after = create_test_task(
            Some(2),
            "Task 1 min after",
            Some(today),
            Some(one_minute_after),
        );
        assert!(
            !checker.is_task_expired(&task_after),
            "Задача на минуту после НЕ должна считаться истёкшей"
        );
    }

    /// Тест: выполненные задачи не считаются истёкшими
    #[test]
    fn test_completed_task_not_expired() {
        let event_bus = EventBus::new(10);
        let checker = DeadlineChecker::new_test(event_bus);

        let now = Utc::now();
        let today = now.date_naive();
        let one_hour_ago = now.time() - Duration::hours(1);

        // Выполненная задача с просроченным дедлайном
        let mut task = create_test_task(Some(1), "Completed task", Some(today), Some(one_hour_ago));
        task.is_done = true;

        assert!(
            !checker.is_task_expired(&task),
            "Выполненная задача НЕ должна считаться истёкшей"
        );
    }

    /// Тест: уже помеченные как истёкшие задачи не считаются
    #[test]
    fn test_already_expired_task_not_rechecked() {
        let event_bus = EventBus::new(10);
        let checker = DeadlineChecker::new_test(event_bus);

        let now = Utc::now();
        let today = now.date_naive();
        let one_hour_ago = now.time() - Duration::hours(1);

        // Задача, уже помеченная как истёкшая
        let mut task = create_test_task(
            Some(1),
            "Already expired task",
            Some(today),
            Some(one_hour_ago),
        );
        task.is_expired = true;

        assert!(
            !checker.is_task_expired(&task),
            "Уже истёкшая задача НЕ должна повторно считаться истёкшей"
        );
    }

    /// Тест: задачи с дедлайном в прошлом
    #[test]
    fn test_deadline_in_past() {
        let event_bus = EventBus::new(10);
        let checker = DeadlineChecker::new_test(event_bus);

        let now = Utc::now();
        let yesterday = now.date_naive() - Duration::days(1);

        // Задача с дедлайном вчера (без времени)
        let task = create_test_task(Some(1), "Task with past date", Some(yesterday), None);

        assert!(
            checker.is_task_expired(&task),
            "Задача с дедлайном вчера должна считаться истёкшей"
        );
    }

    /// Тест мгновенной остановки через CancellationToken
    #[tokio::test]
    async fn test_instant_stop_with_cancellation_token() {
        let event_bus = EventBus::new(10);
        let checker = DeadlineChecker::new_test_async(event_bus).await;

        let cancellation_token = tokio_util::sync::CancellationToken::new();
        let token_clone = cancellation_token.clone();

        // Запускаем проверяльщик в фоне
        let handle = tokio::spawn(async move { checker.run(token_clone).await });

        // Даём проверяльщику время на запуск, затем отменяем
        tokio::time::sleep(std::time::Duration::from_millis(10)).await;
        cancellation_token.cancel();

        // Остановка должна завершиться быстро (< 100мс)
        let start = std::time::Instant::now();
        let result = tokio::time::timeout(std::time::Duration::from_millis(100), handle).await;
        let elapsed = start.elapsed();

        assert!(result.is_ok(), "Остановка должна завершиться без таймаута");
        assert!(
            result.unwrap().is_ok(),
            "Остановка должна завершиться успешно"
        );
        assert!(
            elapsed < std::time::Duration::from_millis(100),
            "Остановка должна быть мгновенной (< 100мс), заняла {:?}",
            elapsed
        );
    }

    /// Интеграционный тест: проверка дедлайнов с реальной БД
    #[tokio::test]
    async fn test_check_deadlines_integration() {
        use tt_db::{NewTask, TaskRepository};

        // Создаём in-memory SQLite
        let pool = sqlx::SqlitePool::connect(":memory:").await.unwrap();

        // Настраиваем таблицы
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
            "#,
        )
        .execute(&pool)
        .await
        .unwrap();

        let task_repository = std::sync::Arc::new(TaskRepository::new(pool.clone()));
        let event_bus = EventBus::new(10);
        let mut rx = event_bus.subscribe();

        // Создаём DeadlineChecker с реальным репозиторием
        let checker = DeadlineChecker::new(event_bus.clone(), task_repository.clone());

        let now = Utc::now();
        let today = now.date_naive();
        let yesterday = today - chrono::Duration::days(1);
        let one_hour_ago = now.time() - chrono::Duration::hours(1);

        // Создаём задачи
        // 1. Истёкшая (вчера)
        task_repository
            .create(NewTask {
                title: "Expired task - yesterday".to_string(),
                description: None,
                created_at: now,
                parent_id: None,
                deadline_date: Some(yesterday),
                deadline_time: None,
                is_done: false,
                is_expired: false,
            })
            .await
            .unwrap();

        // 2. Истёкшая (сегодня час назад)
        task_repository
            .create(NewTask {
                title: "Expired task - today".to_string(),
                description: None,
                created_at: now,
                parent_id: None,
                deadline_date: Some(today),
                deadline_time: Some(one_hour_ago),
                is_done: false,
                is_expired: false,
            })
            .await
            .unwrap();

        // 3. Не истёкшая (завтра)
        let tomorrow = today + chrono::Duration::days(1);
        let one_hour_ahead = now.time() + chrono::Duration::hours(1);
        task_repository
            .create(NewTask {
                title: "Future task".to_string(),
                description: None,
                created_at: now,
                parent_id: None,
                deadline_date: Some(tomorrow),
                deadline_time: Some(one_hour_ahead),
                is_done: false,
                is_expired: false,
            })
            .await
            .unwrap();

        // 4. Выполненная задача с истёкшим дедлайном (не должна считаться)
        task_repository
            .create(NewTask {
                title: "Completed expired task".to_string(),
                description: None,
                created_at: now,
                parent_id: None,
                deadline_date: Some(yesterday),
                deadline_time: None,
                is_done: true,
                is_expired: false,
            })
            .await
            .unwrap();

        // Проверяем дедлайны
        let expired_tasks = checker.check_deadlines().await.unwrap();

        // Должны найти только 2 истёкшие задачи
        assert_eq!(
            expired_tasks.len(),
            2,
            "Должны быть найдены 2 истёкшие задачи"
        );
        assert_eq!(expired_tasks[0].title, "Expired task - yesterday");
        assert_eq!(expired_tasks[1].title, "Expired task - today");

        // Проверяем, что были опубликованы события TasksExpired
        let mut events_received = 0;
        loop {
            match tokio::time::timeout(std::time::Duration::from_millis(100), rx.recv()).await {
                Ok(Ok(tt_core::SystemEvent::TasksExpired {
                    task_id,
                    task_title,
                })) => {
                    events_received += 1;
                    assert!(task_id > 0, "task_id должен быть > 0");
                    assert!(
                        task_title.contains("Expired"),
                        "Заголовок должен содержать Expired"
                    );
                }
                Ok(Ok(_)) => continue,
                Ok(Err(_)) | Err(_) => break,
            }
        }

        assert_eq!(
            events_received, 2,
            "Должны быть опубликованы 2 события TasksExpired"
        );
    }
}
