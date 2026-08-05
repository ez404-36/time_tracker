//! tt-core: домен TimeTracker — типы, события, ошибки, шина.

mod bus;
mod error;
mod events;
mod pomodoro;

// Re-экспорты для публичного API
pub use bus::EventBus;
pub use error::CoreError;
pub use events::{SystemEvent, Value, WindowData};
pub use pomodoro::PomodoroStatus;

// ============================================================================
// Тесты машины состояний Pomodoro и шины событий
// ============================================================================

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;

    // ------------------------------------------------------------------------
    // Тесты валидных переходов
    // ------------------------------------------------------------------------

    #[test]
    fn test_valid_transitions_from_disabled() {
        assert!(PomodoroStatus::Disabled.can_move_to(PomodoroStatus::Working));
    }

    #[test]
    fn test_valid_transitions_from_working() {
        assert!(PomodoroStatus::Working.can_move_to(PomodoroStatus::WorkingPause));
        assert!(PomodoroStatus::Working.can_move_to(PomodoroStatus::WorkingStop));
    }

    #[test]
    fn test_valid_transitions_from_working_pause() {
        assert!(PomodoroStatus::WorkingPause.can_move_to(PomodoroStatus::Working));
    }

    #[test]
    fn test_valid_transitions_from_working_stop() {
        assert!(PomodoroStatus::WorkingStop.can_move_to(PomodoroStatus::Resting));
    }

    #[test]
    fn test_valid_transitions_from_resting() {
        assert!(PomodoroStatus::Resting.can_move_to(PomodoroStatus::RestingPause));
        assert!(PomodoroStatus::Resting.can_move_to(PomodoroStatus::RestingStop));
    }

    #[test]
    fn test_valid_transitions_from_resting_pause() {
        assert!(PomodoroStatus::RestingPause.can_move_to(PomodoroStatus::Resting));
    }

    #[test]
    fn test_valid_transitions_from_resting_stop() {
        assert!(PomodoroStatus::RestingStop.can_move_to(PomodoroStatus::Working));
    }

    // ------------------------------------------------------------------------
    // Тесты запрещённых переходов
    // ------------------------------------------------------------------------

    #[test]
    fn test_invalid_transition_disabled_to_disabled() {
        assert!(!PomodoroStatus::Disabled.can_move_to(PomodoroStatus::Disabled));
    }

    #[test]
    fn test_invalid_transition_disabled_to_resting() {
        assert!(!PomodoroStatus::Disabled.can_move_to(PomodoroStatus::Resting));
    }

    #[test]
    fn test_invalid_transition_working_to_resting() {
        assert!(!PomodoroStatus::Working.can_move_to(PomodoroStatus::Resting));
    }

    #[test]
    fn test_invalid_transition_working_to_working() {
        assert!(!PomodoroStatus::Working.can_move_to(PomodoroStatus::Working));
    }

    #[test]
    fn test_invalid_transition_working_pause_to_resting() {
        assert!(!PomodoroStatus::WorkingPause.can_move_to(PomodoroStatus::Resting));
    }

    #[test]
    fn test_invalid_transition_working_stop_to_working() {
        assert!(!PomodoroStatus::WorkingStop.can_move_to(PomodoroStatus::Working));
    }

    #[test]
    fn test_invalid_transition_resting_to_working() {
        assert!(!PomodoroStatus::Resting.can_move_to(PomodoroStatus::Working));
    }

    #[test]
    fn test_invalid_transition_resting_to_resting() {
        assert!(!PomodoroStatus::Resting.can_move_to(PomodoroStatus::Resting));
    }

    #[test]
    fn test_invalid_transition_resting_pause_to_working() {
        assert!(!PomodoroStatus::RestingPause.can_move_to(PomodoroStatus::Working));
    }

    #[test]
    fn test_invalid_transition_resting_stop_to_resting() {
        assert!(!PomodoroStatus::RestingStop.can_move_to(PomodoroStatus::Resting));
    }

    // ------------------------------------------------------------------------
    // Тесты переходов в Unknown
    // ------------------------------------------------------------------------

    #[test]
    fn test_invalid_transition_any_to_unknown() {
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
    }

    #[test]
    fn test_invalid_transition_unknown_to_any() {
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

    // ------------------------------------------------------------------------
    // Тест stop() из любого статуса
    // ------------------------------------------------------------------------

    #[test]
    fn test_stop_from_any_status() {
        // Из любого активного статуса можно остановиться (перейти в Disabled)
        let active_statuses = [
            PomodoroStatus::Working,
            PomodoroStatus::WorkingPause,
            PomodoroStatus::WorkingStop,
            PomodoroStatus::Resting,
            PomodoroStatus::RestingPause,
            PomodoroStatus::RestingStop,
        ];

        for status in active_statuses {
            assert!(status.can_move_to(PomodoroStatus::Disabled));
        }
    }

    // ------------------------------------------------------------------------
    // Тесты шины событий
    // ------------------------------------------------------------------------

    #[tokio::test]
    async fn test_event_bus_publish_subscribe() {
        let bus = EventBus::new(10);
        let mut rx = bus.subscribe();

        let event = SystemEvent::AppOpen {
            ts: chrono::Utc::now(),
        };
        bus.publish(event.clone());

        let received = rx.recv().await.unwrap();
        assert!(matches!(received, SystemEvent::AppOpen { .. }));
    }

    #[tokio::test]
    async fn test_event_bus_multiple_subscribers() {
        let bus = EventBus::new(10);
        let mut rx1 = bus.subscribe();
        let mut rx2 = bus.subscribe();
        let mut rx3 = bus.subscribe();

        let event = SystemEvent::AppClose {
            ts: chrono::Utc::now(),
        };
        bus.publish(event.clone());

        // Все подписчики должны получить событие
        let received1 = rx1.recv().await.unwrap();
        let received2 = rx2.recv().await.unwrap();
        let received3 = rx3.recv().await.unwrap();

        assert!(matches!(received1, SystemEvent::AppClose { .. }));
        assert!(matches!(received2, SystemEvent::AppClose { .. }));
        assert!(matches!(received3, SystemEvent::AppClose { .. }));
    }

    #[tokio::test]
    async fn test_event_bus_lagged() {
        let bus = EventBus::new(2); // Маленький буфер
        let mut rx = bus.subscribe();

        // Публикуем больше событий, чем ёмкость буфера
        for i in 0..5 {
            bus.publish(SystemEvent::AppChangeSettings {
                values: HashMap::from([("key".to_string(), serde_json::json!(i))]),
            });
        }

        // Подписчик должен получить ошибку RecvError::Lagged
        let result = rx.recv().await;
        match result {
            Ok(_) => {}
            Err(tokio::sync::broadcast::error::RecvError::Lagged(n)) => {
                assert!(n > 0);
            }
            Err(_) => panic!("Expected RecvError::Lagged"),
        }
    }

    #[tokio::test]
    async fn test_event_bus_no_subscribers() {
        let bus = EventBus::new(10);

        // Публикация без подписчиков не должна вызывать панику
        bus.publish(SystemEvent::AppOpen {
            ts: chrono::Utc::now(),
        });
        bus.publish(SystemEvent::AppClose {
            ts: chrono::Utc::now(),
        });

        // Если бы было паника, тест бы не прошёл
    }

    #[tokio::test]
    async fn test_event_bus_multiple_events() {
        let bus = EventBus::new(10);
        let mut rx = bus.subscribe();

        // Публикуем несколько событий разных типов
        bus.publish(SystemEvent::AppOpen {
            ts: chrono::Utc::now(),
        });
        bus.publish(SystemEvent::MainTrackerStart {
            window_tracking: true,
            idle_tracking: true,
            pomodoro_tracking: false,
        });
        bus.publish(SystemEvent::PomodoroTrackerChangeStatus {
            prev_status: PomodoroStatus::Disabled,
            new_status: PomodoroStatus::Working,
        });

        // Принимаем все события
        let event1 = rx.recv().await.unwrap();
        let event2 = rx.recv().await.unwrap();
        let event3 = rx.recv().await.unwrap();

        assert!(matches!(event1, SystemEvent::AppOpen { .. }));
        assert!(matches!(event2, SystemEvent::MainTrackerStart { .. }));
        assert!(matches!(
            event3,
            SystemEvent::PomodoroTrackerChangeStatus { .. }
        ));
    }
}
