//! Аудиоплеер и реализация воспроизведения

use super::error::AudioError;
use super::volume::db_to_linear;
use std::path::Path;
use std::sync::mpsc;
use std::thread;
use tracing::{debug, warn};

use rodio::Source;

/// Команды для аудиопотока
enum AudioCommand {
    Play {
        path: std::path::PathBuf,
        volume_linear: f32,
    },
}

/// Trait для аудиоплеера (позволяет создавать моки для тестов)
pub trait AudioPlayer: Send + Sync {
    /// Воспроизводит аудиофайл с заданной громкостью
    ///
    /// # Arguments
    /// * `path` - путь к аудиофайлу
    /// * `volume_db` - громкость в децибелах (0 = нормальная, отрицательные = тише)
    ///
    /// # Returns
    /// `Ok(())` если воспроизведение запущено успешно
    ///
    /// # Errors
    /// Возвращает `AudioError` если:
    /// - файл не найден
    /// - формат не поддерживается
    /// - аудиоустройство недоступно
    fn play(&self, path: &Path, volume_db: f32) -> Result<(), AudioError>;
}

/// Реализация аудиоплеера на основе rodio
pub struct RodioPlayer {
    sender: mpsc::Sender<AudioCommand>,
}

#[cfg(test)]
/// Мок-реализация для тестов без реального аудиоустройства
pub struct MockPlayer {
    should_fail: bool,
}

#[cfg(test)]
impl MockPlayer {
    /// Создаёт новый мок-плеер
    #[must_use]
    pub fn new(should_fail: bool) -> Self {
        Self { should_fail }
    }
}

#[cfg(test)]
impl AudioPlayer for MockPlayer {
    fn play(&self, path: &Path, _volume_db: f32) -> Result<(), AudioError> {
        if !path.exists() {
            return Err(AudioError::FileNotFound {
                path: path.to_path_buf(),
            });
        }

        if self.should_fail {
            return Err(AudioError::DeviceUnavailable);
        }

        Ok(())
    }
}

impl RodioPlayer {
    /// Создаёт новый экземпляр аудиоплеера
    ///
    /// Запускает отдельный поток для воспроизведения аудио, так как
    /// `rodio::OutputStream` не `Send` и не может использоваться напрямую
    /// в асинхронном контексте.
    ///
    /// # Returns
    /// Экземпляр плеера или ошибку если не удалось инициализировать устройство вывода
    pub fn new() -> Result<Self, AudioError> {
        let (sender, receiver) = mpsc::channel();

        thread::Builder::new()
            .name("audio-player".to_string())
            .spawn(move || {
                // Инициализируем аудиоустройство в отдельном потоке
                let stream_result = rodio::OutputStream::try_default();

                if stream_result.is_err() {
                    warn!("Не удалось инициализировать аудиоустройство");
                    return;
                }

                let (_stream, stream_handle) = stream_result.unwrap();

                // Обрабатываем команды воспроизведения
                while let Ok(cmd) = receiver.recv() {
                    match cmd {
                        AudioCommand::Play {
                            path,
                            volume_linear,
                        } => {
                            if let Err(e) = Self::play_file(&stream_handle, &path, volume_linear) {
                                warn!("Ошибка воспроизведения {}: {}", path.display(), e);
                            }
                        }
                    }
                }
            })
            .map_err(|e| AudioError::DeviceError(format!("Не удалось создать поток: {e}")))?;

        Ok(Self { sender })
    }

    /// Воспроизводит файл с заданным линейным множителем громкости
    fn play_file(
        stream_handle: &rodio::OutputStreamHandle,
        path: &Path,
        volume_linear: f32,
    ) -> Result<(), AudioError> {
        if !path.exists() {
            return Err(AudioError::FileNotFound {
                path: path.to_path_buf(),
            });
        }

        debug!(
            "Воспроизведение файла: {} с громкостью {}",
            path.display(),
            volume_linear
        );

        // Создаём source из файла (rodio с symphonia декодирует mp3/wav/ogg нативно)
        let file = std::fs::File::open(path).map_err(|e| AudioError::IoError {
            path: path.to_path_buf(),
            source: e,
        })?;

        let source = rodio::Decoder::new(file)?;

        // Применяем громкость
        let source = source.amplify(volume_linear);

        // Воспроизводим
        let sink = rodio::Sink::try_new(stream_handle)
            .map_err(|e| AudioError::DeviceError(format!("Не удалось создать Sink: {e}")))?;

        sink.append(source);
        sink.sleep_until_end(); // Блокируем до окончания воспроизведения

        Ok(())
    }
}

impl AudioPlayer for RodioPlayer {
    fn play(&self, path: &Path, volume_db: f32) -> Result<(), AudioError> {
        if !path.exists() {
            return Err(AudioError::FileNotFound {
                path: path.to_path_buf(),
            });
        }

        let volume_linear = db_to_linear(volume_db);

        self.sender
            .send(AudioCommand::Play {
                path: path.to_path_buf(),
                volume_linear,
            })
            .map_err(|e| AudioError::DeviceError(format!("Не удалось отправить команду: {e}")))?;

        Ok(())
    }
}

impl Default for RodioPlayer {
    fn default() -> Self {
        Self::new().expect("Не удалось создать аудиоплеер по умолчанию")
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;
    use tempfile::NamedTempFile;

    #[test]
    fn test_mock_player_file_not_found() {
        let player = MockPlayer::new(false);
        let result = player.play(Path::new("/nonexistent/file.mp3"), 0.0);
        assert!(matches!(result, Err(AudioError::FileNotFound { .. })));
    }

    #[test]
    fn test_mock_player_success() {
        let player = MockPlayer::new(false);

        // Создаём временный файл
        let mut temp_file = NamedTempFile::new().unwrap();
        temp_file.write_all(b"fake audio data").unwrap();

        let result = player.play(temp_file.path(), 0.0);
        assert!(result.is_ok());
    }

    #[test]
    fn test_mock_player_device_unavailable() {
        let player = MockPlayer::new(true);

        let mut temp_file = NamedTempFile::new().unwrap();
        temp_file.write_all(b"fake audio data").unwrap();

        let result = player.play(temp_file.path(), 0.0);
        assert!(matches!(result, Err(AudioError::DeviceUnavailable)));
    }

    #[test]
    fn test_rodio_player_creation() {
        // Проверяем, что создание не паникует даже если устройство недоступно
        let player = RodioPlayer::new();
        // Результат может быть как Ok, так и Err в зависимости от окружения
        // Главное - не должно быть паники
        let _ = player;
    }
}
