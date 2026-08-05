//! Сервис-обёртка для интеграции аудиоплеера с шиной событий

use super::error::AudioError;
use super::player::AudioPlayer;
use std::path::Path;
use std::sync::Arc;
use tracing::warn;
use tt_core::EventBus;
use tt_core::SystemEvent;

/// Сервис аудио с интеграцией в шину событий
pub struct AudioService<P>
where
    P: AudioPlayer + Send + Sync + 'static,
{
    player: Arc<P>,
    event_bus: EventBus,
}

impl<P> AudioService<P>
where
    P: AudioPlayer + Send + Sync + 'static,
{
    /// Создаёт новый сервис аудио
    ///
    /// # Arguments
    /// * `player` - реализация аудиоплеера
    /// * `event_bus` - шина событий для публикации ошибок
    pub fn new(player: P, event_bus: EventBus) -> Self {
        Self {
            player: Arc::new(player),
            event_bus,
        }
    }

    /// Воспроизводит аудиофайл с заданной громкостью и публикует ошибки в шину
    ///
    /// В отличие от `AudioPlayer::play`, этот метод:
    /// - Логирует ошибки через tracing
    /// - Публикует ошибки в шину событий
    /// - Не возвращает ошибки (они обрабатываются внутри)
    ///
    /// # Arguments
    /// * `path` - путь к аудиофайлу
    /// * `volume_db` - громкость в децибелах (0 = нормальная)
    pub fn play(&self, path: &Path, volume_db: f32) {
        if let Err(e) = self.player.play(path, volume_db) {
            self.handle_error(path, &e);
        }
    }

    /// Обрабатывает ошибку воспроизведения
    fn handle_error(&self, path: &Path, error: &AudioError) {
        match error {
            AudioError::FileNotFound { path: _ } => {
                let filename = path
                    .file_name()
                    .and_then(|n| n.to_str())
                    .unwrap_or("unknown");
                self.event_bus.publish(SystemEvent::ErrorFileNotFound {
                    filename: filename.to_string(),
                });
                warn!("Файл не найден: {}", path.display());
            }
            AudioError::UnsupportedFormat { format } => {
                self.event_bus.publish(SystemEvent::ErrorSystem {
                    source: "AudioService".to_string(),
                    error: format!("Неподдерживаемый формат: {}", format),
                });
                warn!("Неподдерживаемый формат файла: {}", format);
            }
            AudioError::IoError { path: _, source } => {
                self.event_bus.publish(SystemEvent::ErrorSystem {
                    source: "AudioService".to_string(),
                    error: format!("Ошибка чтения файла: {}", source),
                });
                warn!("Ошибка чтения файла: {}", source);
            }
            AudioError::DeviceError(msg) | AudioError::DecodeError(msg) => {
                self.event_bus.publish(SystemEvent::ErrorSystem {
                    source: "AudioService".to_string(),
                    error: msg.clone(),
                });
                warn!("Ошибка аудио: {}", msg);
            }
            AudioError::DeviceUnavailable => {
                // Не публикуем событие для недоступного устройства - это не ошибка приложения
                warn!("Аудиоустройство недоступно, воспроизведение пропущено");
            }
        }
    }
}

impl<P> Clone for AudioService<P>
where
    P: AudioPlayer + Send + Sync + 'static,
{
    fn clone(&self) -> Self {
        Self {
            player: Arc::clone(&self.player),
            event_bus: self.event_bus.clone(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::player::MockPlayer;
    use std::io::Write;
    use tempfile::NamedTempFile;

    #[test]
    fn test_audio_service_file_not_found() {
        let event_bus = EventBus::new(10);
        let mut rx = event_bus.subscribe();
        let player = MockPlayer::new(false);
        let service = AudioService::new(player, event_bus);

        service.play(Path::new("/nonexistent/file.mp3"), 0.0);

        // Проверяем, что событие было опубликовано (асинхронно, берём из подписчика)
        tokio::runtime::Runtime::new().unwrap().block_on(async {
            let event = rx.recv().await.unwrap();
            assert!(matches!(event, SystemEvent::ErrorFileNotFound { .. }));
        });
    }

    #[test]
    fn test_audio_service_device_unavailable() {
        let event_bus = EventBus::new(10);
        let player = MockPlayer::new(true);
        let service = AudioService::new(player, event_bus.clone());

        // Создаём временный файл
        let mut temp_file = NamedTempFile::new().unwrap();
        temp_file.write_all(b"fake audio data").unwrap();

        service.play(temp_file.path(), 0.0);

        // DeviceUnavailable не должен публиковаться как ошибка
        let mut rx = event_bus.subscribe();
        tokio::runtime::Runtime::new().unwrap().block_on(async {
            // Должен получить таймаут или RecvError::Lagged, так как событие не публикуется
            let result =
                tokio::time::timeout(std::time::Duration::from_millis(100), rx.recv()).await;
            assert!(
                result.is_err(),
                "Ожидался таймаут (событие не должно публиковаться)"
            );
        });
    }

    #[test]
    fn test_audio_service_success() {
        let event_bus = EventBus::new(10);
        let player = MockPlayer::new(false);
        let service = AudioService::new(player, event_bus.clone());

        let mut temp_file = NamedTempFile::new().unwrap();
        temp_file.write_all(b"fake audio data").unwrap();

        service.play(temp_file.path(), 0.0);

        // При успехе события не публикуются
        let mut rx = event_bus.subscribe();
        tokio::runtime::Runtime::new().unwrap().block_on(async {
            let result =
                tokio::time::timeout(std::time::Duration::from_millis(100), rx.recv()).await;
            assert!(
                result.is_err(),
                "Ожидался таймаут (события не должны публиковаться при успехе)"
            );
        });
    }

    #[test]
    fn test_audio_service_clone() {
        let event_bus = EventBus::new(10);
        let player = MockPlayer::new(false);
        let service = AudioService::new(player, event_bus);

        let service_clone = service.clone();
        // Проверяем, что клон работает и не паникует
        let mut temp_file = NamedTempFile::new().unwrap();
        temp_file.write_all(b"fake audio data").unwrap();

        service_clone.play(temp_file.path(), 0.0);
    }
}
