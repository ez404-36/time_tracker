//! Трекер таймера помодоро

use std::sync::Arc;
use std::time::Duration;
use tokio::sync::Mutex;
use tokio_util::sync::CancellationToken;
use tracing::{debug, error, info};

use tt_core::{EventBus, PomodoroStatus, SystemEvent};

/// Конфигурация таймера помодоро
#[derive(Debug, Clone)]
pub struct PomodoroConfig {
    /// Длительность рабочего интервала в минутах
    pub work_minutes: i16,
    /// Длительность интервала отдыха в минутах
    pub rest_minutes: i16,
}

impl Default for PomodoroConfig {
    fn default() -> Self {
        Self {
            work_minutes: 25,
            rest_minutes: 5,
        }
    }
}

/// Трекер таймера помодоро
///
/// **Ключевое архитектурное изменение:**
///
/// В Python-версии логика таймера была разорвана надвое:
/// - `PomodoroTracker` хранил статус
/// - Таймер жил в UI (`CountdownComponent` в Flet-дереве)
///
/// Последствия:
/// - Закрытие вкладки убивало таймер
/// - Таймер нельзя было протестировать без GUI
/// - `hold()` вызывался из UI-колбэка
///
/// В Rust-версии:
/// - `PomodoroTracker` владеет собственным `tokio::time::interval`
/// - Публикует `PomodoroTick { remaining }` каждую секунду
/// - UI только отображает состояние
/// - Таймер живёт независимо от UI
pub struct PomodoroTracker {
    event_bus: Arc<EventBus>,
    status: PomodoroStatus,
    config: PomodoroConfig,
    running: bool,
    /// Оставшееся время в секундах
    remaining_seconds: i16,
    /// Таймер для отсчёта времени
    timer_handle: Option<tokio::task::JoinHandle<()>>,
    /// CancellationToken для остановки таймера
    timer_cancellation_token: Option<CancellationToken>,
}

impl PomodoroTracker {
    /// Создаёт новый экземпляр трекера помодоро
    pub fn new(event_bus: Arc<EventBus>, config: PomodoroConfig) -> Self {
        Self {
            event_bus,
            status: PomodoroStatus::Disabled,
            config,
            running: false,
            remaining_seconds: 0,
            timer_handle: None,
            timer_cancellation_token: None,
        }
    }

    /// Запускает рабочий интервал
    pub async fn start_working(&mut self) -> Result<(), crate::TrackerError> {
        if !self.running {
            return Err(crate::TrackerError::PomodoroNotRunning);
        }

        let new_status = PomodoroStatus::Working;
        self._change_status(new_status)?;
        self.remaining_seconds = self.config.work_minutes * 60;
        self._start_timer()?;

        info!(
            "Запуск рабочего интервала помодоро ({} минут)",
            self.config.work_minutes
        );

        Ok(())
    }

    /// Запускает интервал отдыха
    pub async fn start_resting(&mut self) -> Result<(), crate::TrackerError> {
        if !self.running {
            return Err(crate::TrackerError::PomodoroNotRunning);
        }

        let new_status = PomodoroStatus::Resting;
        self._change_status(new_status)?;
        self.remaining_seconds = self.config.rest_minutes * 60;
        self._start_timer()?;

        info!(
            "Запуск интервала отдыха помодоро ({} минут)",
            self.config.rest_minutes
        );

        Ok(())
    }

    /// Приостанавливает текущий таймер
    pub async fn pause(&mut self) -> Result<(), crate::TrackerError> {
        if !self.running {
            return Err(crate::TrackerError::PomodoroNotRunning);
        }

        let new_status = match self.status {
            PomodoroStatus::Working => PomodoroStatus::WorkingPause,
            PomodoroStatus::Resting => PomodoroStatus::RestingPause,
            _ => {
                error!(
                    "Невозможно приостановить таймер в статусе {:?}",
                    self.status
                );
                return Err(crate::TrackerError::InvalidPomodoroTransition(
                    format!("{:?}", self.status),
                    format!("{:?}Pause", self.status),
                ));
            }
        };

        self._change_status(new_status)?;
        self._stop_timer()?;

        info!("Таймер помодоро приостановлен");

        Ok(())
    }

    /// Возобновляет приостановленный таймер
    pub async fn resume(&mut self) -> Result<(), crate::TrackerError> {
        if !self.running {
            return Err(crate::TrackerError::PomodoroNotRunning);
        }

        let new_status = match self.status {
            PomodoroStatus::WorkingPause => PomodoroStatus::Working,
            PomodoroStatus::RestingPause => PomodoroStatus::Resting,
            _ => {
                error!("Невозможно возобновить таймер в статусе {:?}", self.status);
                return Err(crate::TrackerError::InvalidPomodoroTransition(
                    format!("{:?}", self.status),
                    format!("{:?}", self.status).replace("Pause", ""),
                ));
            }
        };

        self._change_status(new_status)?;
        self._start_timer()?;

        info!("Таймер помодоро возобновлён");

        Ok(())
    }

    /// Завершает текущий интервал (вызывается при истечении таймера)
    pub async fn hold(&mut self) -> Result<(), crate::TrackerError> {
        if !self.running {
            return Err(crate::TrackerError::PomodoroNotRunning);
        }

        let new_status = match self.status {
            PomodoroStatus::Working => PomodoroStatus::WorkingStop,
            PomodoroStatus::Resting => PomodoroStatus::RestingStop,
            _ => {
                error!("Невозможно завершить интервал в статусе {:?}", self.status);
                return Err(crate::TrackerError::InvalidPomodoroTransition(
                    format!("{:?}", self.status),
                    format!("{:?}Stop", self.status),
                ));
            }
        };

        self._change_status(new_status)?;
        self._stop_timer()?;

        info!("Интервал помодоро завершён");

        Ok(())
    }

    /// Полностью останавливает таймер помодоро
    pub async fn stop(&mut self) -> Result<(), crate::TrackerError> {
        self.running = false;
        self._change_status(PomodoroStatus::Disabled)?;
        self._stop_timer()?;

        info!("Таймер помодоро полностью остановлен");

        Ok(())
    }

    /// Запускает трекер (начинает с рабочего интервала)
    pub async fn start(&mut self) -> Result<(), crate::TrackerError> {
        if self.running {
            return Ok(());
        }

        self.running = true;
        self.start_working().await?;

        Ok(())
    }

    /// Возвращает текущий статус
    #[must_use]
    pub const fn status(&self) -> PomodoroStatus {
        self.status
    }

    /// Возвращает оставшееся время в секундах
    #[must_use]
    pub const fn remaining_seconds(&self) -> i16 {
        self.remaining_seconds
    }

    /// Проверяет, запущен ли трекер
    #[must_use]
    pub const fn is_running(&self) -> bool {
        self.running
    }

    /// Изменяет статус с проверкой машины переходов
    fn _change_status(&mut self, new_status: PomodoroStatus) -> Result<(), crate::TrackerError> {
        if !self.status.can_move_to(new_status) {
            let prev = format!("{:?}", self.status);
            let next = format!("{:?}", new_status);
            error!(
                "Недопустимый переход статуса помодоро: {} -> {}",
                prev, next
            );

            // Публикуем ошибку в шину событий
            self.event_bus.publish(SystemEvent::ErrorSystem {
                source: "PomodoroTracker".to_string(),
                error: format!("Невозможен переход: {} -> {}", prev, next),
            });

            return Err(crate::TrackerError::InvalidPomodoroTransition(prev, next));
        }

        let prev_status = self.status;
        self.status = new_status;

        debug!(
            "Статус помодоро изменён: {:?} -> {:?}",
            prev_status, new_status
        );

        // Публикуем событие изменения статуса
        self.event_bus
            .publish(SystemEvent::PomodoroTrackerChangeStatus {
                prev_status,
                new_status,
            });

        Ok(())
    }

    /// Запускает таймер отсчёта
    fn _start_timer(&mut self) -> Result<(), crate::TrackerError> {
        self._stop_timer()?;

        let cancellation_token = CancellationToken::new();
        let token_clone = cancellation_token.clone();

        let _event_bus = self.event_bus.clone();
        let remaining_seconds = Arc::new(Mutex::new(self.remaining_seconds));

        let handle = tokio::spawn(async move {
            let mut interval = tokio::time::interval(Duration::from_secs(1));

            loop {
                tokio::select! {
                    _ = token_clone.cancelled() => {
                        debug!("Таймер помодоро получил сигнал отмены");
                        break;
                    }
                    _ = interval.tick() => {
                        let mut seconds = remaining_seconds.lock().await;

                        if *seconds > 0 {
                            *seconds -= 1;

                            // Публикуем тик таймера
                            _event_bus.publish(SystemEvent::PomodoroTick {
                                remaining: *seconds,
                            });
                            debug!("Осталось времени: {} сек", *seconds);
                        } else {
                            debug!("Таймер помодоро истёк");
                            break;
                        }
                    }
                }
            }
        });

        self.timer_handle = Some(handle);
        self.timer_cancellation_token = Some(cancellation_token);

        Ok(())
    }

    /// Останавливает таймер
    fn _stop_timer(&mut self) -> Result<(), crate::TrackerError> {
        if let Some(cancellation_token) = self.timer_cancellation_token.take() {
            cancellation_token.cancel();
        }

        if let Some(handle) = self.timer_handle.take() {
            // Не ждём завершения — таймер должен быть быстрым
            handle.abort();
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Arc;

    /// Тест состояния по умолчанию
    #[test]
    fn test_default_status() {
        let event_bus = Arc::new(EventBus::new(10));
        let config = PomodoroConfig::default();

        let tracker = PomodoroTracker::new(event_bus, config);

        assert_eq!(tracker.status(), PomodoroStatus::Disabled);
        assert!(!tracker.is_running());
        assert_eq!(tracker.remaining_seconds(), 0);
    }

    /// Тест запуска рабочего интервала
    #[tokio::test]
    async fn test_start_working() {
        let event_bus = Arc::new(EventBus::new(10));
        let config = PomodoroConfig {
            work_minutes: 25,
            rest_minutes: 5,
        };

        let mut tracker = PomodoroTracker::new(event_bus.clone(), config);

        // Сначала запускаем трекер
        tracker.start().await.unwrap();

        assert_eq!(tracker.status(), PomodoroStatus::Working);
        assert_eq!(tracker.remaining_seconds(), 25 * 60);
        assert!(tracker.is_running());
    }

    /// Тест приостановки и возобновления
    #[tokio::test]
    async fn test_pause_and_resume() {
        let event_bus = Arc::new(EventBus::new(10));
        let config = PomodoroConfig::default();

        let mut tracker = PomodoroTracker::new(event_bus.clone(), config);

        tracker.start().await.unwrap();
        let remaining = tracker.remaining_seconds();

        tracker.pause().await.unwrap();
        assert_eq!(tracker.status(), PomodoroStatus::WorkingPause);
        assert_eq!(tracker.remaining_seconds(), remaining);

        tracker.resume().await.unwrap();
        assert_eq!(tracker.status(), PomodoroStatus::Working);
        assert_eq!(tracker.remaining_seconds(), remaining);
    }

    /// Тест запрета неверных переходов
    #[test]
    fn test_invalid_transitions() {
        let event_bus = Arc::new(EventBus::new(10));
        let config = PomodoroConfig::default();

        let mut tracker = PomodoroTracker::new(event_bus, config);

        // Неизвестный статус → не должен быть возможен
        assert!(matches!(
            tracker._change_status(PomodoroStatus::Unknown),
            Err(crate::TrackerError::InvalidPomodoroTransition(_, _))
        ));

        // Disabled → Resting (должен быть только Working)
        assert!(matches!(
            tracker._change_status(PomodoroStatus::Resting),
            Err(crate::TrackerError::InvalidPomodoroTransition(_, _))
        ));
    }

    /// Тест машины состояний с использованием can_move_to
    #[tokio::test]
    async fn test_state_machine() {
        let event_bus = Arc::new(EventBus::new(10));
        let config = PomodoroConfig::default();

        let mut tracker = PomodoroTracker::new(event_bus, config);

        // Disabled -> Working (разрешено)
        assert!(PomodoroStatus::Disabled.can_move_to(PomodoroStatus::Working));

        // После start() статус должен быть Working
        tracker.start().await.unwrap();
        assert_eq!(tracker.status(), PomodoroStatus::Working);

        // Working -> WorkingPause (разрешено)
        assert!(PomodoroStatus::Working.can_move_to(PomodoroStatus::WorkingPause));
        tracker.pause().await.unwrap();
        assert_eq!(tracker.status(), PomodoroStatus::WorkingPause);

        // WorkingPause -> Working (разрешено)
        assert!(PomodoroStatus::WorkingPause.can_move_to(PomodoroStatus::Working));
        tracker.resume().await.unwrap();
        assert_eq!(tracker.status(), PomodoroStatus::Working);

        // Working -> WorkingStop (разрешено)
        assert!(PomodoroStatus::Working.can_move_to(PomodoroStatus::WorkingStop));
        tracker.hold().await.unwrap();
        assert_eq!(tracker.status(), PomodoroStatus::WorkingStop);

        // WorkingStop -> Resting (разрешено)
        assert!(PomodoroStatus::WorkingStop.can_move_to(PomodoroStatus::Resting));
        tracker.start_resting().await.unwrap();
        assert_eq!(tracker.status(), PomodoroStatus::Resting);

        // Resting -> RestingPause (разрешено)
        assert!(PomodoroStatus::Resting.can_move_to(PomodoroStatus::RestingPause));
        tracker.pause().await.unwrap();
        assert_eq!(tracker.status(), PomodoroStatus::RestingPause);

        // RestingPause -> Resting (разрешено)
        assert!(PomodoroStatus::RestingPause.can_move_to(PomodoroStatus::Resting));
        tracker.resume().await.unwrap();
        assert_eq!(tracker.status(), PomodoroStatus::Resting);

        // Resting -> RestingStop (разрешено)
        assert!(PomodoroStatus::Resting.can_move_to(PomodoroStatus::RestingStop));
        tracker.hold().await.unwrap();
        assert_eq!(tracker.status(), PomodoroStatus::RestingStop);

        // RestingStop -> Working (разрешено)
        assert!(PomodoroStatus::RestingStop.can_move_to(PomodoroStatus::Working));
        tracker.start_working().await.unwrap();
        assert_eq!(tracker.status(), PomodoroStatus::Working);

        // Любой активный статус -> Disabled (разрешено через stop())
        assert!(PomodoroStatus::Working.can_move_to(PomodoroStatus::Disabled));
        tracker.stop().await.unwrap();
        assert_eq!(tracker.status(), PomodoroStatus::Disabled);
    }

    /// Тест публикации событий при изменении статуса
    #[tokio::test]
    async fn test_status_change_events() {
        let event_bus = Arc::new(EventBus::new(10));
        let mut rx = event_bus.subscribe();
        let config = PomodoroConfig::default();

        let mut tracker = PomodoroTracker::new(event_bus.clone(), config);

        tracker.start().await.unwrap();

        // Проверяем событие изменения статуса
        let event = tokio::time::timeout(Duration::from_millis(100), rx.recv()).await;
        assert!(event.is_ok(), "Должно быть событие изменения статуса");

        if let Ok(Ok(SystemEvent::PomodoroTrackerChangeStatus {
            prev_status,
            new_status,
        })) = event
        {
            assert_eq!(prev_status, PomodoroStatus::Disabled);
            assert_eq!(new_status, PomodoroStatus::Working);
        } else {
            panic!("Ожидается PomodoroTrackerChangeStatus");
        }
    }

    /// Тест ошибки при попытке приостановить не запущенный таймер
    #[tokio::test]
    async fn test_pause_not_running() {
        let event_bus = Arc::new(EventBus::new(10));
        let config = PomodoroConfig::default();

        let mut tracker = PomodoroTracker::new(event_bus, config);

        // Не запущен — ошибка
        assert!(matches!(
            tracker.pause().await,
            Err(crate::TrackerError::PomodoroNotRunning)
        ));
    }

    /// Тест запрета переходов в/из Unknown
    #[test]
    fn test_unknown_status_forbidden() {
        // Из любого статуса в Unknown запрещён
        let all_statuses = [
            PomodoroStatus::Disabled,
            PomodoroStatus::Working,
            PomodoroStatus::WorkingPause,
            PomodoroStatus::WorkingStop,
            PomodoroStatus::Resting,
            PomodoroStatus::RestingPause,
            PomodoroStatus::RestingStop,
        ];

        for status in all_statuses {
            assert!(!status.can_move_to(PomodoroStatus::Unknown));
        }

        // Из Unknown в любой статус запрещён
        let all_statuses = [
            PomodoroStatus::Disabled,
            PomodoroStatus::Working,
            PomodoroStatus::WorkingPause,
            PomodoroStatus::WorkingStop,
            PomodoroStatus::Resting,
            PomodoroStatus::RestingPause,
            PomodoroStatus::RestingStop,
        ];

        for status in all_statuses {
            assert!(!PomodoroStatus::Unknown.can_move_to(status));
        }
    }
}
