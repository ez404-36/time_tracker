//! Отслеживание активного окна и списка открытых окон

use std::collections::HashSet;
use std::sync::Arc;
use tokio_util::sync::CancellationToken;
use tracing::{debug, info, warn};

use tt_core::{EventBus, SystemEvent, WindowData};
use tt_db::{NewWindowSession, SessionRepository};
use tt_platform::WindowControl;

use crate::error::TrackerError;

/// Ключ для хеширования окна (игнорируем PID при сравнении)
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub(crate) struct WindowKey {
    executable_name: String,
    window_title: Option<String>,
    executable_path: Option<String>,
}

impl From<&WindowData> for WindowKey {
    fn from(data: &WindowData) -> Self {
        Self {
            executable_name: data.executable_name.clone(),
            window_title: data.window_title.clone(),
            executable_path: data.executable_path.clone(),
        }
    }
}

/// Трекер активных окон
///
/// Отслеживает активное окно и список открытых окон. Публикует события
/// при смене активного окна или изменении списка открытых окон.
///
/// ## Исправление бага B1
///
/// В Python-версии было:
/// ```python
/// if len(new_active_windows) != self.active_windows:  # BUG: int vs list
/// ```
///
/// Это условие всегда было истинным, поэтому событие отправлялось каждую секунду.
/// В Rust используется корректное сравнение множеств через `HashSet<WindowKey>`,
/// что исключает false positives.
pub struct WindowTracker {
    event_bus: Arc<EventBus>,
    session_repository: Arc<SessionRepository>,
    window_control: Arc<dyn WindowControl>,
    running: bool,
    current_window: Option<WindowData>,
    current_session_id: Option<i64>,
    current_session_start_ts: Option<chrono::DateTime<chrono::Utc>>,
    active_windows: HashSet<WindowKey>,
    cancellation_token: Option<CancellationToken>,
}

impl WindowTracker {
    /// Создаёт новый экземпляр трекера окон
    pub fn new(
        event_bus: Arc<EventBus>,
        session_repository: Arc<SessionRepository>,
        window_control: Box<dyn WindowControl>,
    ) -> Self {
        Self {
            event_bus,
            session_repository,
            window_control: window_control.into(),
            running: false,
            current_window: None,
            current_session_id: None,
            current_session_start_ts: None,
            active_windows: HashSet::new(),
            cancellation_token: None,
        }
    }

    /// Запускает трекер окон
    pub async fn start(&mut self) -> Result<(), TrackerError> {
        if self.running {
            return Ok(());
        }

        self.running = true;
        let cancellation_token = CancellationToken::new();
        self.cancellation_token = Some(cancellation_token.clone());

        let event_bus = self.event_bus.clone();
        let window_control = self.window_control.clone();
        let session_repository = self.session_repository.clone();
        let mut current_window = self.current_window.clone();
        let mut current_session_id = self.current_session_id;
        let mut current_session_start_ts = self.current_session_start_ts;
        let mut active_windows = self.active_windows.clone();

        tokio::spawn(async move {
            let mut interval = tokio::time::interval(tokio::time::Duration::from_secs(1));

            loop {
                tokio::select! {
                    _ = cancellation_token.cancelled() => {
                        debug!("WindowTracker получил сигнал остановки");
                        break;
                    }
                    _ = interval.tick() => {
                        if let Ok(windows) = window_control.all_windows() {
                            let new_windows_set: HashSet<WindowKey> =
                                windows.iter().map(WindowKey::from).collect();

                            // Проверяем изменение списка открытых окон
                            if new_windows_set != active_windows {
                                active_windows = new_windows_set.clone();
                                event_bus.publish(SystemEvent::WindowTrackerChangeOpenedWindows {
                                    active_windows: windows,
                                });
                            }

                            if let Ok(Some(active_window)) = window_control.active_window() {
                                if current_window.as_ref() != Some(&active_window) {
                                    debug!(
                                        "Активное окно изменилось: {:?} -> {:?}",
                                        current_window, active_window
                                    );

                                    // Завершаем предыдущую сессию, если была
                                    if let Some(start_ts) = current_session_start_ts.take() {
                                        if let Some(session_id) = current_session_id.take() {
                                            let end_ts = chrono::Utc::now();
                                            let delta = end_ts - start_ts;

                                            // Исправление бага B3: используем num_seconds() вместо .seconds
                                            let duration = delta.num_seconds().max(0);

                                            if let Err(e) = session_repository.update_window(
                                                session_id,
                                                end_ts,
                                                duration,
                                            ).await {
                                                warn!("Не удалось завершить сессию окна {}: {}", session_id, e);
                                            }
                                        }
                                    }

                                    current_window = Some(active_window.clone());

                                    // Создаём новую сессию
                                    let start_ts = chrono::Utc::now();
                                    let new_session = NewWindowSession {
                                        start_ts,
                                        end_ts: None,
                                        duration: 0,
                                        executable_name: active_window.executable_name.clone(),
                                        executable_path: active_window.executable_path.clone(),
                                        window_title: active_window.window_title.clone(),
                                    };

                                    match session_repository.create_window(new_session).await {
                                        Ok(session) => {
                                            current_session_id = session.id;
                                            current_session_start_ts = Some(start_ts);
                                        }
                                        Err(e) => {
                                            warn!("Не удалось создать сессию для окна {}: {}",
                                                  active_window.executable_name, e);
                                        }
                                    }

                                    event_bus.publish(SystemEvent::WindowTrackerSwitchWindow {
                                        window: active_window,
                                        ts: chrono::Utc::now(),
                                    });
                                }
                            }
                        }
                    }
                }
            }

            // При остановке закрываем текущую сессию, если есть
            if let (Some(session_id), Some(start_ts)) =
                (current_session_id, current_session_start_ts)
            {
                let end_ts = chrono::Utc::now();
                let delta = end_ts - start_ts;
                let duration = delta.num_seconds().max(0);

                if let Err(e) = session_repository
                    .update_window(session_id, end_ts, duration)
                    .await
                {
                    warn!(
                        "Не удалось завершить сессию окна при остановке {}: {}",
                        session_id, e
                    );
                }
            }
        });

        info!("WindowTracker запущен");
        Ok(())
    }

    /// Останавливает трекер окон
    pub async fn stop(&mut self) -> Result<(), TrackerError> {
        if !self.running {
            return Ok(());
        }

        self.running = false;

        if let Some(cancellation_token) = self.cancellation_token.take() {
            cancellation_token.cancel();
        }

        info!("WindowTracker остановлен");
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use sqlx::SqlitePool;
    use std::sync::Arc;
    use tt_core::SystemEvent;
    use tt_db::WindowSession;

    /// Мок для WindowControl
    struct MockWindowControl {
        active_window: Option<WindowData>,
        active_windows: Vec<WindowData>,
    }

    impl MockWindowControl {
        fn new() -> Self {
            Self {
                active_window: None,
                active_windows: Vec::new(),
            }
        }

        fn set_active_window(&mut self, window: WindowData) {
            self.active_window = Some(window);
        }

        fn _set_active_windows(&mut self, windows: Vec<WindowData>) {
            self.active_windows = windows;
        }
    }

    impl WindowControl for MockWindowControl {
        fn active_window(&self) -> Result<Option<WindowData>, tt_platform::PlatformError> {
            Ok(self.active_window.clone())
        }

        fn all_windows(&self) -> Result<Vec<WindowData>, tt_platform::PlatformError> {
            Ok(self.active_windows.clone())
        }

        fn idle_seconds(&self) -> Result<u64, tt_platform::PlatformError> {
            Ok(0)
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
            CREATE TABLE IF NOT EXISTS window_session (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_ts DATETIME NOT NULL,
                end_ts DATETIME,
                duration INTEGER NOT NULL,
                executable_name VARCHAR(255) NOT NULL,
                executable_path VARCHAR(255),
                window_title VARCHAR(255)
            );
            "#,
        )
        .execute(pool)
        .await
        .unwrap();
    }

    /// Тест создания WindowTracker
    #[tokio::test]
    async fn test_window_tracker_creation() {
        let event_bus = Arc::new(EventBus::new(10));
        let mock_window_control = Box::new(MockWindowControl::new());
        let pool = create_test_pool().await;
        let session_repository = Arc::new(SessionRepository::new(pool));
        let _tracker = WindowTracker::new(event_bus, session_repository, mock_window_control);
    }

    /// Тест бага B1: событие не должно публиковаться, если список окон не изменился
    #[tokio::test]
    async fn test_bug_b1_no_event_on_unchanged_windows() {
        let event_bus = Arc::new(EventBus::new(10));
        let mut rx = event_bus.subscribe();

        let pool = create_test_pool().await;
        setup_test_db(&pool).await;
        let session_repository = Arc::new(SessionRepository::new(pool));

        let mock_window_control = Box::new(MockWindowControl::new());

        // В моке мы не можем изменить состояние после передачи в трекер,
        // поэтому тест проверяет только отсутствие событий при неизменном состоянии

        let mut tracker =
            WindowTracker::new(event_bus.clone(), session_repository, mock_window_control);

        // Запускаем трекер
        tracker.start().await.unwrap();

        // Ждём немного, чтобы трекер успел проверить состояние
        tokio::time::sleep(tokio::time::Duration::from_millis(150)).await;

        // Проверяем, что не было события изменения окон
        let result = tokio::time::timeout(tokio::time::Duration::from_millis(100), rx.recv()).await;
        assert!(
            result.is_err(),
            "Не должно быть события WindowTrackerChangeOpenedWindows при неизменном списке"
        );

        tracker.stop().await.unwrap();
    }

    /// Тест переключения активного окна
    #[tokio::test]
    async fn test_switch_active_window() {
        let event_bus = Arc::new(EventBus::new(10));
        let mut rx = event_bus.subscribe();

        let pool = create_test_pool().await;
        setup_test_db(&pool).await;
        let session_repository = Arc::new(SessionRepository::new(pool));

        let mut mock_window_control = Box::new(MockWindowControl::new());

        let window1 = WindowData {
            executable_name: "code".to_string(),
            window_title: Some("VS Code".to_string()),
            executable_path: Some("/usr/bin/code".to_string()),
            pid: Some(1234),
        };
        mock_window_control.set_active_window(window1);

        let mut tracker =
            WindowTracker::new(event_bus.clone(), session_repository, mock_window_control);

        tracker.start().await.unwrap();

        // Ждём события WindowTrackerSwitchWindow
        let result = tokio::time::timeout(tokio::time::Duration::from_millis(500), rx.recv()).await;
        assert!(result.is_ok(), "Должно быть событие переключения окна");

        if let Ok(Ok(SystemEvent::WindowTrackerSwitchWindow { window, .. })) = result {
            assert_eq!(window.executable_name, "code");
        } else {
            panic!("Ожидается WindowTrackerSwitchWindow");
        }

        tracker.stop().await.unwrap();
    }

    /// Интеграционный тест: сессия создаётся в БД при активном окне
    #[tokio::test]
    async fn test_window_session_created() {
        use std::sync::Mutex;

        // Изменяемый мок для управления активным окном
        struct MutableMockWindowControl {
            active_window: Arc<Mutex<Option<WindowData>>>,
        }

        impl MutableMockWindowControl {
            fn new(active_window: Arc<Mutex<Option<WindowData>>>) -> Self {
                Self { active_window }
            }
        }

        impl WindowControl for MutableMockWindowControl {
            fn active_window(&self) -> Result<Option<WindowData>, tt_platform::PlatformError> {
                Ok(self.active_window.lock().unwrap().clone())
            }

            fn all_windows(&self) -> Result<Vec<WindowData>, tt_platform::PlatformError> {
                Ok(Vec::new())
            }

            fn idle_seconds(&self) -> Result<u64, tt_platform::PlatformError> {
                Ok(0)
            }
        }

        let event_bus = Arc::new(EventBus::new(10));
        let pool = create_test_pool().await;
        setup_test_db(&pool).await;
        let session_repository = Arc::new(SessionRepository::new(pool));

        let active_window_arc = Arc::new(Mutex::new(None::<WindowData>));
        let mock_window_control =
            Box::new(MutableMockWindowControl::new(active_window_arc.clone()));

        let mut tracker = WindowTracker::new(
            event_bus.clone(),
            session_repository.clone(),
            mock_window_control,
        );

        tracker.start().await.unwrap();

        // Устанавливаем активное окно
        let window = WindowData {
            executable_name: "firefox".to_string(),
            window_title: Some("GitHub - Mozilla Firefox".to_string()),
            executable_path: Some("/usr/bin/firefox".to_string()),
            pid: Some(5678),
        };
        active_window_arc.lock().unwrap().replace(window.clone());

        // Ждём, пока трекер создаст сессию (цикл работает каждую секунду)
        tokio::time::sleep(tokio::time::Duration::from_secs(2)).await;

        // Проверяем, что сессия создана в БД
        let sessions = sqlx::query_as::<_, WindowSession>(
            "SELECT id, start_ts, end_ts, duration, executable_name, executable_path, window_title FROM window_session"
        )
        .fetch_all(session_repository.pool())
        .await
        .unwrap();

        assert_eq!(sessions.len(), 1, "Должна быть создана одна сессия");
        let session = &sessions[0];

        assert!(session.id.is_some(), "ID сессии должен быть установлен");
        assert_eq!(session.executable_name, "firefox");
        assert_eq!(
            session.window_title,
            Some("GitHub - Mozilla Firefox".to_string())
        );
        assert_eq!(
            session.executable_path,
            Some("/usr/bin/firefox".to_string())
        );
        assert!(
            session.end_ts.is_none(),
            "end_ts должен быть NULL для активной сессии"
        );
        assert_eq!(
            session.duration, 0,
            "duration должен быть 0 для активной сессии"
        );

        tracker.stop().await.unwrap();
    }

    /// Интеграционный тест: смена окна закрывает предыдущую сессию
    #[tokio::test]
    async fn test_window_session_closed_on_switch() {
        use std::sync::Mutex;

        struct MutableMockWindowControl {
            active_window: Arc<Mutex<Option<WindowData>>>,
        }

        impl MutableMockWindowControl {
            fn new(active_window: Arc<Mutex<Option<WindowData>>>) -> Self {
                Self { active_window }
            }
        }

        impl WindowControl for MutableMockWindowControl {
            fn active_window(&self) -> Result<Option<WindowData>, tt_platform::PlatformError> {
                Ok(self.active_window.lock().unwrap().clone())
            }

            fn all_windows(&self) -> Result<Vec<WindowData>, tt_platform::PlatformError> {
                Ok(Vec::new())
            }

            fn idle_seconds(&self) -> Result<u64, tt_platform::PlatformError> {
                Ok(0)
            }
        }

        let event_bus = Arc::new(EventBus::new(10));
        let pool = create_test_pool().await;
        setup_test_db(&pool).await;
        let session_repository = Arc::new(SessionRepository::new(pool));

        let active_window_arc = Arc::new(Mutex::new(None::<WindowData>));
        let mock_window_control =
            Box::new(MutableMockWindowControl::new(active_window_arc.clone()));

        let mut tracker = WindowTracker::new(
            event_bus.clone(),
            session_repository.clone(),
            mock_window_control,
        );

        tracker.start().await.unwrap();

        // Устанавливаем первое окно
        let window1 = WindowData {
            executable_name: "code".to_string(),
            window_title: Some("VS Code - project".to_string()),
            executable_path: Some("/usr/bin/code".to_string()),
            pid: Some(1234),
        };
        active_window_arc.lock().unwrap().replace(window1.clone());

        // Ждём создания первой сессии
        tokio::time::sleep(tokio::time::Duration::from_secs(2)).await;

        // Переключаемся на другое окно
        let window2 = WindowData {
            executable_name: "firefox".to_string(),
            window_title: Some("Google".to_string()),
            executable_path: Some("/usr/bin/firefox".to_string()),
            pid: Some(5678),
        };
        active_window_arc.lock().unwrap().replace(window2.clone());

        // Ждём создания второй сессии
        tokio::time::sleep(tokio::time::Duration::from_secs(2)).await;

        // Проверяем сессии в БД
        let sessions = sqlx::query_as::<_, WindowSession>(
            "SELECT id, start_ts, end_ts, duration, executable_name, executable_path, window_title FROM window_session ORDER BY start_ts"
        )
        .fetch_all(session_repository.pool())
        .await
        .unwrap();

        assert_eq!(sessions.len(), 2, "Должны быть две сессии");

        // Первая сессия должна быть закрыта
        let first_session = &sessions[0];
        assert_eq!(first_session.executable_name, "code");
        assert!(
            first_session.end_ts.is_some(),
            "Первая сессия должна быть закрыта"
        );
        assert!(first_session.duration > 0, "duration должен быть > 0");

        // Вторая сессия должна быть активной (ещё не закрыта)
        let second_session = &sessions[1];
        assert_eq!(second_session.executable_name, "firefox");
        assert!(
            second_session.end_ts.is_none(),
            "Вторая сессия должна быть активной"
        );

        tracker.stop().await.unwrap();
    }

    /// Интеграционный тест: остановка трекера закрывает открытую сессию
    #[tokio::test]
    async fn test_window_session_closed_on_stop() {
        use std::sync::Mutex;

        struct MutableMockWindowControl {
            active_window: Arc<Mutex<Option<WindowData>>>,
        }

        impl MutableMockWindowControl {
            fn new(active_window: Arc<Mutex<Option<WindowData>>>) -> Self {
                Self { active_window }
            }
        }

        impl WindowControl for MutableMockWindowControl {
            fn active_window(&self) -> Result<Option<WindowData>, tt_platform::PlatformError> {
                Ok(self.active_window.lock().unwrap().clone())
            }

            fn all_windows(&self) -> Result<Vec<WindowData>, tt_platform::PlatformError> {
                Ok(Vec::new())
            }

            fn idle_seconds(&self) -> Result<u64, tt_platform::PlatformError> {
                Ok(0)
            }
        }

        let event_bus = Arc::new(EventBus::new(10));
        let pool = create_test_pool().await;
        setup_test_db(&pool).await;
        let session_repository = Arc::new(SessionRepository::new(pool));

        let active_window_arc = Arc::new(Mutex::new(None::<WindowData>));
        let mock_window_control =
            Box::new(MutableMockWindowControl::new(active_window_arc.clone()));

        let mut tracker = WindowTracker::new(
            event_bus.clone(),
            session_repository.clone(),
            mock_window_control,
        );

        tracker.start().await.unwrap();

        // Устанавливаем активное окно
        let window = WindowData {
            executable_name: "terminal".to_string(),
            window_title: Some("bash - zsh".to_string()),
            executable_path: Some("/usr/bin/zsh".to_string()),
            pid: Some(9999),
        };
        active_window_arc.lock().unwrap().replace(window.clone());

        // Ждём создания сессии
        tokio::time::sleep(tokio::time::Duration::from_secs(2)).await;

        // Останавливаем трекер
        tracker.stop().await.unwrap();

        // Ждём, пока задача остановки завершится
        tokio::time::sleep(tokio::time::Duration::from_millis(200)).await;

        // Проверяем, что сессия закрыта
        let sessions = sqlx::query_as::<_, WindowSession>(
            "SELECT id, start_ts, end_ts, duration, executable_name, executable_path, window_title FROM window_session"
        )
        .fetch_all(session_repository.pool())
        .await
        .unwrap();

        assert_eq!(sessions.len(), 1, "Должна быть одна сессия");
        let session = &sessions[0];

        assert_eq!(session.executable_name, "terminal");
        assert!(
            session.end_ts.is_some(),
            "Сессия должна быть закрыта при остановке"
        );
        assert!(session.duration > 0, "duration должен быть > 0");
    }
}
