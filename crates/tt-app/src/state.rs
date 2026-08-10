//! Управление состоянием приложения

use dioxus::prelude::*;
use std::sync::Arc;
use tt_core::{EventBus, PomodoroStatus, SystemEvent};
use tt_db::Settings;
use tt_tracker::MainTracker;

/// Раздел навигации
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum NavSection {
    Tasks,
    Tracker,
    Statistics,
    Settings,
}

/// Состояние приложения
///
/// Заменяет Python SessionStore. Все данные хранятся в сигналах Dioxus,
/// которые автоматически обновляют UI при изменении.
pub struct AppState {
    pub event_bus: Arc<EventBus>,
    pub settings: Settings,
    pub main_tracker: MainTracker,
    pub theme: Signal<Theme>,
    pub pomodoro_status: Signal<PomodoroStatus>,
    pub pomodoro_remaining: Signal<i16>,
}

impl AppState {
    pub fn new(
        event_bus: Arc<EventBus>,
        settings: Settings,
        main_tracker: MainTracker,
        initial_theme: Theme,
    ) -> Self {
        let theme = Signal::new(initial_theme);
        let pomodoro_status = Signal::new(PomodoroStatus::Disabled);
        let pomodoro_remaining = Signal::new(0);

        Self {
            event_bus,
            settings,
            main_tracker,
            theme,
            pomodoro_status,
            pomodoro_remaining,
        }
    }

    /// Запускает фоновую задачу для чтения событий из шины
    ///
    /// Примечание: сигналы Dioxus не Send, поэтому прямой доступ к ним из tokio::spawn невозможен.
    /// Для полной интеграции требуется использование каналов (mpsc/broadcast) для коммуникации
    /// между фоновыми задачами и UI-потоком. Это будет реализовано при необходимости.
    pub fn start_event_listener(&self) {
        let event_bus = self.event_bus.clone();

        tokio::spawn(async move {
            let mut rx = event_bus.subscribe();

            loop {
                match rx.recv().await {
                    Ok(event) => match event {
                        SystemEvent::ErrorSystem { source, error } => {
                            tracing::error!("System error [{}]: {}", source, error);
                        }
                        SystemEvent::ErrorWrongConfig { field, error } => {
                            tracing::error!("Config error [{}]: {}", field, error);
                        }
                        SystemEvent::ErrorFileNotFound { filename } => {
                            tracing::warn!("File not found: {}", filename);
                        }
                        _ => {}
                    },
                    Err(tokio::sync::broadcast::error::RecvError::Lagged(n)) => {
                        tracing::warn!("Event bus lagged by {} messages", n);
                    }
                    Err(tokio::sync::broadcast::error::RecvError::Closed) => {
                        tracing::info!("Event bus closed, stopping listener");
                        break;
                    }
                }
            }
        });
    }
}

/// Тема приложения
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Theme {
    Light,
    Dark,
}

impl Theme {
    pub fn toggle(&self) -> Self {
        match self {
            Theme::Light => Theme::Dark,
            Theme::Dark => Theme::Light,
        }
    }

    pub fn as_str(&self) -> &str {
        match self {
            Theme::Light => "light",
            Theme::Dark => "dark",
        }
    }
}
