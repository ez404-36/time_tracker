//! Оркестратор всех трекеров

use std::sync::Arc;
use tracing::{info, warn};

use tt_core::{EventBus, SystemEvent};

use crate::{IdleTracker, PomodoroTracker, WindowTracker};

/// Параметры работы основного трекера
#[derive(Debug, Clone, Copy)]
pub struct MainTrackerParams {
    /// Отслеживать активные окна
    pub window_tracking: bool,
    /// Отслеживать бездействие
    pub idle_tracking: bool,
    /// Использовать таймер помодоро
    pub pomodoro_tracking: bool,
}

impl Default for MainTrackerParams {
    fn default() -> Self {
        Self {
            window_tracking: true,
            idle_tracking: true,
            pomodoro_tracking: false,
        }
    }
}

/// Оркестратор всех трекеров
///
/// Отвечает за координацию работы трекеров окон, бездействия и помодоро.
/// Публикует события старта/остановки/паузы/возобновления.
pub struct MainTracker {
    event_bus: Arc<EventBus>,
    window_tracker: Option<WindowTracker>,
    idle_tracker: Option<IdleTracker>,
    pomodoro_tracker: Option<PomodoroTracker>,
    params: MainTrackerParams,
    running: bool,
    paused: bool,
}

impl MainTracker {
    /// Создаёт новый экземпляр основного трекера
    pub fn new(event_bus: Arc<EventBus>) -> Self {
        Self {
            event_bus,
            window_tracker: None,
            idle_tracker: None,
            pomodoro_tracker: None,
            params: MainTrackerParams::default(),
            running: false,
            paused: false,
        }
    }

    /// Устанавливает трекер окон
    pub fn set_window_tracker(&mut self, tracker: WindowTracker) {
        self.window_tracker = Some(tracker);
    }

    /// Устанавливает трекер бездействия
    pub fn set_idle_tracker(&mut self, tracker: IdleTracker) {
        self.idle_tracker = Some(tracker);
    }

    /// Устанавливает трекер помодоро
    pub fn set_pomodoro_tracker(&mut self, tracker: PomodoroTracker) {
        self.pomodoro_tracker = Some(tracker);
    }

    /// Запускает основной трекер с указанными параметрами
    pub async fn start(&mut self, params: MainTrackerParams) {
        if self.running {
            warn!("MainTracker уже запущен");
            return;
        }

        info!(
            "Запуск MainTracker: window={}, idle={}, pomodoro={}",
            params.window_tracking, params.idle_tracking, params.pomodoro_tracking
        );

        self.params = params;
        self.running = true;
        self.paused = false;

        // Публикуем событие старта
        self.event_bus.publish(SystemEvent::MainTrackerStart {
            window_tracking: params.window_tracking,
            idle_tracking: params.idle_tracking,
            pomodoro_tracking: params.pomodoro_tracking,
        });

        // Запускаем трекеры
        if params.window_tracking {
            if let Some(ref mut tracker) = self.window_tracker {
                if let Err(e) = tracker.start().await {
                    warn!("Не удалось запустить WindowTracker: {}", e);
                }
            }
        }

        if params.idle_tracking {
            if let Some(ref mut tracker) = self.idle_tracker {
                if let Err(e) = tracker.start().await {
                    warn!("Не удалось запустить IdleTracker: {}", e);
                }
            }
        }

        if params.pomodoro_tracking {
            if let Some(ref mut tracker) = self.pomodoro_tracker {
                if let Err(e) = tracker.start().await {
                    warn!("Не удалось запустить PomodoroTracker: {}", e);
                }
            }
        }
    }

    /// Останавливает основной трекер
    pub async fn stop(&mut self) {
        if !self.running {
            warn!("MainTracker не запущен");
            return;
        }

        info!("Остановка MainTracker");

        // Останавливаем все трекеры
        if let Some(ref mut tracker) = self.window_tracker {
            if let Err(e) = tracker.stop().await {
                warn!("Не удалось остановить WindowTracker: {}", e);
            }
        }

        if let Some(ref mut tracker) = self.idle_tracker {
            tracker.stop().await;
        }

        if let Some(ref mut tracker) = self.pomodoro_tracker {
            if let Err(e) = tracker.stop().await {
                warn!("Не удалось остановить PomodoroTracker: {}", e);
            }
        }

        self.running = false;
        self.paused = false;

        // Публикуем событие остановки
        self.event_bus.publish(SystemEvent::MainTrackerStop);
    }

    /// Приостанавливает основной трекер (ручная пауза)
    pub async fn pause(&mut self) {
        if !self.running {
            warn!("MainTracker не запущен");
            return;
        }

        if self.paused {
            warn!("MainTracker уже на паузе");
            return;
        }

        info!("MainTracker на паузе");

        self.paused = true;

        // Публикуем событие паузы
        self.event_bus.publish(SystemEvent::MainTrackerPause);

        // Приостанавливаем трекер помодоро, если запущен
        if let Some(ref mut tracker) = self.pomodoro_tracker {
            if let Err(e) = tracker.pause().await {
                warn!("Не удалось приостановить PomodoroTracker: {}", e);
            }
        }
    }

    /// Приостанавливает основной трекер (автоматическая пауза при истечении таймера)
    pub async fn hold(&mut self) {
        if !self.running {
            warn!("MainTracker не запущен");
            return;
        }

        info!("MainTracker на автоматической паузе (hold)");

        self.paused = true;

        // Публикуем событие hold
        self.event_bus.publish(SystemEvent::MainTrackerHold);

        // Вызываем hold на трекере помодоро
        if let Some(ref mut tracker) = self.pomodoro_tracker {
            if let Err(e) = tracker.hold().await {
                warn!("Не удалось выполнить hold на PomodoroTracker: {}", e);
            }
        }
    }

    /// Возобновляет работу основного трекера
    pub async fn resume(&mut self) {
        if !self.paused {
            warn!("MainTracker не на паузе");
            return;
        }

        info!("Возобновление MainTracker");

        self.paused = false;

        // Публикуем событие возобновления
        self.event_bus.publish(SystemEvent::MainTrackerResume);

        // Возобновляем трекер помодоро, если был на паузе
        if let Some(ref mut tracker) = self.pomodoro_tracker {
            if let Err(e) = tracker.resume().await {
                warn!("Не удалось возобновить PomodoroTracker: {}", e);
            }
        }
    }

    /// Обновляет параметры работы
    pub fn update_params(&mut self, params: MainTrackerParams) {
        info!(
            "Обновление параметров MainTracker: window={}, idle={}, pomodoro={}",
            params.window_tracking, params.idle_tracking, params.pomodoro_tracking
        );

        self.params = params;

        // Применение изменений к запущенным трекерам требует сложной логики:
        // - WindowTracker: не требует перезапуска при смене настроек
        // - IdleTracker: нужно изменить порог (idle_threshold) без остановки
        // - PomodoroTracker: нужно изменить тайминги (work_minutes, rest_minutes) без остановки
        //
        // Текущая архитектура не предусматривает горячую перезагрузку настроек без полной
        // остановки и запуска трекеров. Для полной реализации требуется:
        // 1. Добавить методы set_idle_threshold() в IdleTracker (уже есть)
        // 2. Добавить методы set_work_minutes() / set_rest_minutes() в PomodoroTracker
        // 3. Обновить update_params() для вызова этих методов при изменении соответствующих параметров
        //
        // На данный момент новые настройки применяются только при следующем запуске через start().
        // Это упрощение, которое допустимо для текущей версии, так как настройки обычно меняются
        // редко и при явном действии пользователя через UI.
    }

    /// Проверяет, запущен ли основной трекер
    #[must_use]
    pub const fn is_running(&self) -> bool {
        self.running
    }

    /// Проверяет, находится ли основной трекер на паузе
    #[must_use]
    pub const fn is_paused(&self) -> bool {
        self.paused
    }

    /// Возвращает текущие параметры
    #[must_use]
    pub const fn params(&self) -> MainTrackerParams {
        self.params
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Arc;

    /// Тест создания по умолчанию
    #[test]
    fn test_default_creation() {
        let event_bus = Arc::new(EventBus::new(10));
        let tracker = MainTracker::new(event_bus);

        assert!(!tracker.is_running());
        assert!(!tracker.is_paused());

        let params = tracker.params();
        assert!(params.window_tracking);
        assert!(params.idle_tracking);
        assert!(!params.pomodoro_tracking);
    }

    /// Тест запуска с параметрами
    #[tokio::test]
    async fn test_start_with_params() {
        let event_bus = Arc::new(EventBus::new(10));
        let mut tracker = MainTracker::new(event_bus.clone());

        let params = MainTrackerParams {
            window_tracking: true,
            idle_tracking: false,
            pomodoro_tracking: true,
        };

        tracker.start(params).await;

        assert!(tracker.is_running());
        assert!(!tracker.is_paused());

        let new_params = tracker.params();
        assert!(new_params.window_tracking);
        assert!(!new_params.idle_tracking);
        assert!(new_params.pomodoro_tracking);
    }

    /// Тест повторного запуска
    #[tokio::test]
    async fn test_double_start() {
        let event_bus = Arc::new(EventBus::new(10));
        let mut tracker = MainTracker::new(event_bus);

        tracker.start(MainTrackerParams::default()).await;
        tracker.start(MainTrackerParams::default()).await;

        // Должен остаться запущенным, без ошибок
        assert!(tracker.is_running());
    }

    /// Тест остановки без запуска
    #[tokio::test]
    async fn test_stop_without_start() {
        let event_bus = Arc::new(EventBus::new(10));
        let mut tracker = MainTracker::new(event_bus);

        tracker.stop().await;

        // Должен остаться незапущенным, без ошибок
        assert!(!tracker.is_running());
    }

    /// Тест паузы и возобновления
    #[tokio::test]
    async fn test_pause_and_resume() {
        let event_bus = Arc::new(EventBus::new(10));
        let mut tracker = MainTracker::new(event_bus);

        tracker.start(MainTrackerParams::default()).await;
        tracker.pause().await;

        assert!(tracker.is_running());
        assert!(tracker.is_paused());

        tracker.resume().await;

        assert!(tracker.is_running());
        assert!(!tracker.is_paused());
    }

    /// Тест повторной паузы
    #[tokio::test]
    async fn test_double_pause() {
        let event_bus = Arc::new(EventBus::new(10));
        let mut tracker = MainTracker::new(event_bus);

        tracker.set_running(true);
        tracker.pause().await;
        tracker.pause().await;

        // Должен остаться на паузе, без ошибок
        assert!(tracker.is_paused());
    }

    /// Тест возобновления без паузы
    #[tokio::test]
    async fn test_resume_without_pause() {
        let event_bus = Arc::new(EventBus::new(10));
        let mut tracker = MainTracker::new(event_bus);

        tracker.set_running(true);
        tracker.resume().await;

        // Должен остаться не на паузе, без ошибок
        assert!(!tracker.is_paused());
    }

    /// Тест hold
    #[tokio::test]
    async fn test_hold() {
        let event_bus = Arc::new(EventBus::new(10));
        let mut tracker = MainTracker::new(event_bus);

        tracker.set_running(true);
        tracker.hold().await;

        assert!(tracker.is_running());
        assert!(tracker.is_paused());
    }

    /// Тест публикации событий
    #[tokio::test]
    async fn test_event_publication() {
        let event_bus = Arc::new(EventBus::new(10));
        let mut rx = event_bus.subscribe();
        let mut tracker = MainTracker::new(event_bus.clone());

        // Запуск
        tracker.start(MainTrackerParams::default()).await;
        let event1 = tokio::time::timeout(std::time::Duration::from_millis(100), rx.recv()).await;
        assert!(event1.is_ok());
        assert!(matches!(
            event1.unwrap().unwrap(),
            SystemEvent::MainTrackerStart { .. }
        ));

        // Пауза
        tracker.pause().await;
        let event2 = tokio::time::timeout(std::time::Duration::from_millis(100), rx.recv()).await;
        assert!(event2.is_ok());
        assert!(matches!(
            event2.unwrap().unwrap(),
            SystemEvent::MainTrackerPause
        ));

        // Возобновление
        tracker.resume().await;
        let event3 = tokio::time::timeout(std::time::Duration::from_millis(100), rx.recv()).await;
        assert!(event3.is_ok());
        assert!(matches!(
            event3.unwrap().unwrap(),
            SystemEvent::MainTrackerResume
        ));

        // Остановка
        tracker.stop().await;
        let event4 = tokio::time::timeout(std::time::Duration::from_millis(100), rx.recv()).await;
        assert!(event4.is_ok());
        assert!(matches!(
            event4.unwrap().unwrap(),
            SystemEvent::MainTrackerStop
        ));
    }

    /// Вспомогательный метод для тестов
    impl MainTracker {
        pub fn set_running(&mut self, running: bool) {
            self.running = running;
        }
    }
}
