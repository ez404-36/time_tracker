//! Отслеживание бездействия пользователя

use std::sync::Arc;
use std::time::Duration;
use tokio_util::sync::CancellationToken;
use tracing::{debug, error, info, warn};

use tt_core::{EventBus, SystemEvent};
use tt_db::{NewIdleSession, SessionRepository};
use tt_platform::WindowControl;

/// Трекер бездействия пользователя
///
/// Отслеживает время бездействия через `WindowControl::idle_seconds()`.
/// Порог берётся из настроек. Публикует события при обнаружении и завершении бездействия.
/// Записывает сессии бездействия в базу данных.
pub struct IdleTracker {
    event_bus: Arc<EventBus>,
    session_repository: Arc<SessionRepository>,
    window_control: Box<dyn WindowControl>,
    idle_threshold: u64,
    is_idle: bool,
    current_session_id: Option<i64>,
    current_session_start_ts: Option<chrono::DateTime<chrono::Utc>>,
}

impl IdleTracker {
    /// Создаёт новый экземпляр трекера бездействия
    pub fn new(
        event_bus: Arc<EventBus>,
        session_repository: Arc<SessionRepository>,
        window_control: Box<dyn WindowControl>,
        idle_threshold: u64,
    ) -> Self {
        Self {
            event_bus,
            session_repository,
            window_control,
            idle_threshold,
            is_idle: false,
            current_session_id: None,
            current_session_start_ts: None,
        }
    }

    /// Запускает трекер
    pub async fn start(&mut self) -> Result<(), String> {
        info!("Запуск IdleTracker (порог: {} сек)", self.idle_threshold);

        self.event_bus.publish(SystemEvent::ActivityTrackerStart);

        Ok(())
    }

    /// Останавливает трекер
    pub async fn stop(&mut self) {
        info!("Остановка IdleTracker");

        // Закрываем текущую сессию бездействия, если есть
        if let (Some(session_id), Some(start_ts)) = (
            self.current_session_id.take(),
            self.current_session_start_ts.take(),
        ) {
            let end_ts = chrono::Utc::now();
            let delta = end_ts - start_ts;
            let duration = delta.num_seconds().max(0);

            if let Err(e) = self
                .session_repository
                .update_idle(session_id, end_ts, duration)
                .await
            {
                warn!(
                    "Не удалось завершить сессию бездействия при остановке {}: {}",
                    session_id, e
                );
            }
        }

        self.event_bus.publish(SystemEvent::ActivityTrackerStop);
        self._reset_state();
    }

    /// Основной цикл работы трекера
    ///
    /// Использует `tokio::select!` с `CancellationToken` для мгновенной остановки.
    pub async fn run(&mut self, cancellation_token: CancellationToken) -> Result<(), String> {
        let mut interval = tokio::time::interval(Duration::from_secs(1));

        loop {
            tokio::select! {
                _ = cancellation_token.cancelled() => {
                    debug!("IdleTracker получил сигнал отмены");
                    break;
                }
                _ = interval.tick() => {
                    if let Err(e) = self._tick().await {
                        error!("Ошибка в IdleTracker: {}", e);
                    }
                }
            }
        }

        Ok(())
    }

    /// Выполняет один такт работы трекера
    async fn _tick(&mut self) -> Result<(), tt_platform::PlatformError> {
        let idle_seconds = self.window_control.idle_seconds()?;
        let now = chrono::Utc::now();

        debug!(
            "Время бездействия: {} сек (порог: {} сек)",
            idle_seconds, self.idle_threshold
        );

        if idle_seconds >= self.idle_threshold && !self.is_idle {
            self._on_detect_idle(now).await;
        } else if idle_seconds < self.idle_threshold && self.is_idle {
            self._end_idle(now).await;
        }

        Ok(())
    }

    /// Обрабатывает обнаружение бездействия
    async fn _on_detect_idle(&mut self, ts: chrono::DateTime<chrono::Utc>) {
        debug!("Обнаружено бездействие пользователя");
        self.is_idle = true;

        // Создаём сессию бездействия в БД
        let new_session = NewIdleSession {
            start_ts: ts,
            end_ts: None,
            duration: 0,
        };

        match self.session_repository.create_idle(new_session).await {
            Ok(session) => {
                self.current_session_id = session.id;
                self.current_session_start_ts = Some(ts);
            }
            Err(e) => {
                warn!("Не удалось создать сессию бездействия: {}", e);
            }
        }

        self.event_bus
            .publish(SystemEvent::ActivityTrackerDetectIdle { ts });
    }

    /// Обрабатывает завершение бездействия
    async fn _end_idle(&mut self, ts: chrono::DateTime<chrono::Utc>) {
        debug!("Завершено бездействие пользователя");
        self.is_idle = false;

        // Закрываем сессию бездействия в БД
        if let (Some(session_id), Some(start_ts)) = (
            self.current_session_id.take(),
            self.current_session_start_ts.take(),
        ) {
            let delta = ts - start_ts;
            let duration = delta.num_seconds().max(0);

            if let Err(e) = self
                .session_repository
                .update_idle(session_id, ts, duration)
                .await
            {
                warn!(
                    "Не удалось завершить сессию бездействия {}: {}",
                    session_id, e
                );
            }
        }

        self.event_bus
            .publish(SystemEvent::ActivityTrackerStopIdle { ts });
    }

    /// Сбрасывает состояние трекера
    fn _reset_state(&mut self) {
        self.is_idle = false;
    }

    /// Устанавливает порог бездействия
    pub fn set_idle_threshold(&mut self, threshold: u64) {
        self.idle_threshold = threshold;
    }

    /// Возвращает текущий порог бездействия
    #[must_use]
    pub const fn idle_threshold(&self) -> u64 {
        self.idle_threshold
    }

    /// Проверяет, находится ли пользователь в бездействии
    #[must_use]
    pub const fn is_idle(&self) -> bool {
        self.is_idle
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use sqlx::SqlitePool;
    use std::sync::Mutex;

    /// Мок-реализация WindowControl для тестов
    struct MockWindowControl {
        idle_seconds: Arc<Mutex<u64>>,
    }

    impl MockWindowControl {
        fn new(idle_seconds: Arc<Mutex<u64>>) -> Self {
            Self { idle_seconds }
        }

        fn _set_idle_seconds(&self, seconds: u64) {
            *self.idle_seconds.lock().unwrap() = seconds;
        }
    }

    impl WindowControl for MockWindowControl {
        fn active_window(&self) -> Result<Option<tt_core::WindowData>, tt_platform::PlatformError> {
            Ok(None)
        }

        fn all_windows(&self) -> Result<Vec<tt_core::WindowData>, tt_platform::PlatformError> {
            Ok(Vec::new())
        }

        fn idle_seconds(&self) -> Result<u64, tt_platform::PlatformError> {
            Ok(*self.idle_seconds.lock().unwrap())
        }
    }

    /// Создаёт in-memory pool для тестов
    async fn create_test_pool() -> SqlitePool {
        sqlx::SqlitePool::connect(":memory:").await.unwrap()
    }

    /// Создаёт таблицы для тестов
    async fn setup_test_db(pool: &SqlitePool) {
        sqlx::query(
            r#"
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

    /// Тест обнаружения бездействия
    #[tokio::test]
    async fn test_detect_idle() {
        let event_bus = Arc::new(EventBus::new(10));
        let mut rx = event_bus.subscribe();
        let idle_seconds = Arc::new(Mutex::new(10u64));

        let mock_window_control = Box::new(MockWindowControl::new(idle_seconds));
        let pool = create_test_pool().await;
        setup_test_db(&pool).await;
        let session_repository = Arc::new(SessionRepository::new(pool));

        let mut tracker = IdleTracker::new(
            event_bus.clone(),
            session_repository,
            mock_window_control,
            5, // порог 5 сек
        );

        tracker.start().await.unwrap();

        // Выполняем тик
        tracker._tick().await.unwrap();

        // Пропускаем все события до ActivityTrackerDetectIdle
        loop {
            let event = tokio::time::timeout(Duration::from_millis(100), rx.recv()).await;
            match event {
                Ok(Ok(SystemEvent::ActivityTrackerDetectIdle { ts })) => {
                    let now = chrono::Utc::now();
                    assert!(
                        now - ts < chrono::Duration::seconds(1),
                        "Временная метка должна быть актуальной"
                    );
                    break; // нашли нужное событие
                }
                Ok(Ok(_other)) => {
                    // Пропускаем другие события (например, ActivityTrackerStart)
                    continue;
                }
                Ok(Err(_)) | Err(_) => {
                    panic!("Должно быть событие обнаружения бездействия");
                }
            }
        }

        assert!(tracker.is_idle(), "Трекер должен считаться бездействующим");
    }

    /// Тест завершения бездействия
    #[tokio::test]
    async fn test_end_idle() {
        let event_bus = Arc::new(EventBus::new(10));
        let mut rx = event_bus.subscribe();
        let idle_seconds = Arc::new(Mutex::new(10u64));
        let idle_clone = idle_seconds.clone();

        let mock_window_control = Box::new(MockWindowControl::new(idle_seconds));
        let pool = create_test_pool().await;
        setup_test_db(&pool).await;
        let session_repository = Arc::new(SessionRepository::new(pool));

        let mut tracker = IdleTracker::new(
            event_bus.clone(),
            session_repository,
            mock_window_control,
            5, // порог 5 сек
        );

        tracker.start().await.unwrap();

        // Выполняем тик с высоким значением
        tracker._tick().await.unwrap();

        // Пропускаем ActivityTrackerStart, затем ищем ActivityTrackerDetectIdle
        loop {
            let event = tokio::time::timeout(Duration::from_millis(100), rx.recv()).await;
            match event {
                Ok(Ok(SystemEvent::ActivityTrackerDetectIdle { .. })) => {
                    break; // нашли нужное событие
                }
                Ok(Ok(SystemEvent::ActivityTrackerStart)) => {
                    // Пропускаем ActivityTrackerStart
                    continue;
                }
                Ok(Ok(_other)) => {
                    // Пропускаем другие события
                    continue;
                }
                Ok(Err(_)) | Err(_) => {
                    panic!("Должно быть событие обнаружения бездействия");
                }
            }
        }

        // Устанавливаем бездействие ниже порога через клон Arc
        *idle_clone.lock().unwrap() = 2;
        tracker._tick().await.unwrap();

        // Пропускаем все события до ActivityTrackerStopIdle
        loop {
            let event = tokio::time::timeout(Duration::from_millis(100), rx.recv()).await;
            match event {
                Ok(Ok(SystemEvent::ActivityTrackerStopIdle { .. })) => {
                    break; // нашли нужное событие
                }
                Ok(Ok(_)) => {
                    // Пропускаем другие события
                    continue;
                }
                Ok(Err(_)) | Err(_) => {
                    panic!("Должно быть событие завершения бездействия");
                }
            }
        }

        assert!(
            !tracker.is_idle(),
            "Трекер НЕ должен считаться бездействующим"
        );
    }

    /// Тест отсутствия событий при стабильном состоянии
    #[tokio::test]
    async fn test_no_events_when_stable() {
        let event_bus = Arc::new(EventBus::new(10));
        let mut rx = event_bus.subscribe();
        let idle_seconds = Arc::new(Mutex::new(10u64));

        let mock_window_control = Box::new(MockWindowControl::new(idle_seconds));
        let pool = create_test_pool().await;
        setup_test_db(&pool).await;
        let session_repository = Arc::new(SessionRepository::new(pool));

        let mut tracker = IdleTracker::new(
            event_bus.clone(),
            session_repository,
            mock_window_control,
            5, // порог 5 сек
        );

        tracker.start().await.unwrap();

        // Выполняем тик
        tracker._tick().await.unwrap();

        // Пропускаем все события (ActivityTrackerStart и другие)
        while tokio::time::timeout(Duration::from_millis(10), rx.recv())
            .await
            .is_ok()
        {}

        // Выполняем ещё несколько тиков с тем же значением — событий не должно быть
        for _ in 0..3 {
            tracker._tick().await.unwrap();
        }

        // Проверяем, что новых событий нет
        let event = tokio::time::timeout(Duration::from_millis(100), rx.recv()).await;
        assert!(
            event.is_err(),
            "Не должно быть новых событий при стабильном состоянии"
        );
    }

    /// Тест мгновенной остановки через CancellationToken
    #[tokio::test]
    async fn test_instant_stop_with_cancellation_token() {
        let event_bus = Arc::new(EventBus::new(10));
        let idle_seconds = Arc::new(Mutex::new(0u64));
        let mock_window_control = Box::new(MockWindowControl::new(idle_seconds));
        let pool = create_test_pool().await;
        setup_test_db(&pool).await;
        let session_repository = Arc::new(SessionRepository::new(pool));

        let mut tracker = IdleTracker::new(event_bus, session_repository, mock_window_control, 5);

        tracker.start().await.unwrap();

        let cancellation_token = CancellationToken::new();
        let token_clone = cancellation_token.clone();

        // Запускаем трекер в фоне
        let handle = tokio::spawn(async move { tracker.run(token_clone).await });

        // Даём трекеру время на запуск, затем отменяем
        tokio::time::sleep(Duration::from_millis(10)).await;
        cancellation_token.cancel();

        // Остановка должна завершиться быстро (< 100мс)
        let start = std::time::Instant::now();
        let result = tokio::time::timeout(Duration::from_millis(100), handle).await;
        let elapsed = start.elapsed();

        assert!(result.is_ok(), "Остановка должна завершиться без таймаута");
        assert!(
            result.unwrap().is_ok(),
            "Остановка должна завершиться успешно"
        );
        assert!(
            elapsed < Duration::from_millis(100),
            "Остановка должна быть мгновенной (< 100мс), заняла {:?}",
            elapsed
        );
    }

    /// Тест изменения порога бездействия
    #[tokio::test]
    async fn test_change_idle_threshold() {
        let event_bus = Arc::new(EventBus::new(10));
        let mut rx = event_bus.subscribe();
        let idle_seconds = Arc::new(Mutex::new(7u64));
        let idle_clone = idle_seconds.clone();

        let mock_window_control = Box::new(MockWindowControl::new(idle_seconds));
        let pool = create_test_pool().await;
        setup_test_db(&pool).await;
        let session_repository = Arc::new(SessionRepository::new(pool));

        let mut tracker = IdleTracker::new(
            event_bus.clone(),
            session_repository,
            mock_window_control,
            5, // начальный порог 5 сек
        );

        tracker.start().await.unwrap();

        // Выполняем тик с значением 7 (> 5)
        tracker._tick().await.unwrap();

        // С порогом 5 сек — должно быть событие ActivityTrackerDetectIdle
        // Пропускаем ActivityTrackerStart и ищем ActivityTrackerDetectIdle
        loop {
            let event1 = tokio::time::timeout(Duration::from_millis(100), rx.recv()).await;
            match event1 {
                Ok(Ok(SystemEvent::ActivityTrackerDetectIdle { .. })) => {
                    break; // нашли нужное событие
                }
                Ok(Ok(_)) => {
                    // Пропускаем ActivityTrackerStart и другие события
                    continue;
                }
                _ => {
                    panic!("Должно быть событие обнаружения бездействия с порогом 5 сек");
                }
            }
        }

        // Меняем порог на 10 сек
        tracker.set_idle_threshold(10);

        // С новым порогом 10 сек — событие ActivityTrackerStopIdle должно быть (7 < 10)
        tracker._tick().await.unwrap();

        // Проверяем, что пришло событие ActivityTrackerStopIdle
        loop {
            let event2 = tokio::time::timeout(Duration::from_millis(100), rx.recv()).await;
            match event2 {
                Ok(Ok(SystemEvent::ActivityTrackerStopIdle { .. })) => {
                    break; // нашли нужное событие
                }
                Ok(Ok(_)) => {
                    // Пропускаем другие события
                    continue;
                }
                _ => {
                    panic!("Должно быть событие завершения бездействия при смене порога");
                }
            }
        }

        // Теперь тик с тем же значением (7 < 10) — событий не должно быть
        tracker._tick().await.unwrap();

        let event3 = tokio::time::timeout(Duration::from_millis(100), rx.recv()).await;
        assert!(
            event3.is_err(),
            "Не должно быть события с тем же значением после смены порога"
        );

        // Устанавливаем бездействие ниже нового порога
        *idle_clone.lock().unwrap() = 5;
        tracker._tick().await.unwrap();

        // Не должно быть события, так как уже не в бездействии
        let event4 = tokio::time::timeout(Duration::from_millis(100), rx.recv()).await;
        assert!(
            event4.is_err(),
            "Не должно быть события, так как уже не в бездействии"
        );
    }
}
