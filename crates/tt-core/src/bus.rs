//! Шина событий на основе tokio::sync::broadcast

use super::events::SystemEvent;

/// Шина событий на основе tokio::sync::broadcast
///
/// Реализует паттерн pub/sub: несколько подписчиков получают
/// копии всех опубликованных событий.
///
/// При переполнении буфера старые сообщения удаляются, а подписчики
/// получают ошибку RecvError::Lagged. Это ожидаемое поведение,
/// которое логируется на уровне warn.
#[derive(Clone)]
pub struct EventBus {
    tx: tokio::sync::broadcast::Sender<SystemEvent>,
}

impl EventBus {
    /// Создаёт новую шину событий с заданной ёмкостью
    ///
    /// # Arguments
    /// * `capacity` - количество последних событий, хранящихся в буфере
    ///
    /// # Panics
    /// Паникует если `capacity` равен 0 (требование tokio::sync::broadcast)
    #[must_use]
    pub fn new(capacity: usize) -> Self {
        let (tx, _) = tokio::sync::broadcast::channel(capacity);
        Self { tx }
    }

    /// Подписывается на получение событий
    ///
    /// Возвращает Receiver, который будет получать копии всех
    /// событий, опубликованных после подписки.
    ///
    /// # Returns
    /// `broadcast::Receiver<SystemEvent>` для приёма событий
    #[must_use]
    pub fn subscribe(&self) -> tokio::sync::broadcast::Receiver<SystemEvent> {
        self.tx.subscribe()
    }

    /// Публикует событие в шину
    ///
    /// Событие будет доставлено всем активным подписчикам.
    /// Если нет подписчиков, событие игнорируется.
    ///
    /// # Arguments
    /// * `event` - событие для публикации
    pub fn publish(&self, event: SystemEvent) {
        match self.tx.send(event) {
            Ok(_) => {}
            Err(tokio::sync::broadcast::error::SendError(_)) => {
                // Нет подписчиков — игнорируем
            }
        }
    }
}
