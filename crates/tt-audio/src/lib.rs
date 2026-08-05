//! tt-audio: крейт для воспроизведения аудио в TimeTracker
//!
//! Реализует асинхронное воспроизведение аудиофайлов с поддержкой форматов
//! mp3, wav, ogg через библиотеку `rodio` с бэкендом `symphonia`.
//!
//! ## Особенности
//!
//! - Нативное декодирование mp3/wav/ogg без внешнего ffmpeg
//! - Асинхронное воспроизведение (не блокирует вызывающий код)
//! - Поддержка громкости в децибелах (совместимо с pydub)
//! - Интеграция с шиной событий `tt-core` для обработки ошибок
//! - Graceful degradation при отсутствии аудиоустройства
//!
//! ## Архитектура
//!
//! Крейт состоит из нескольких слоёв:
//!
//! - `error` - типы ошибок аудио-операций
//! - `volume` - конвертация громкости из децибел в линейный множитель
//! - `player` - trait `AudioPlayer` и его реализация через `rodio`
//! - `service` - сервис-обёртка для интеграции с шиной событий
//!
//! ## Пример использования
//!
//! ```ignore
//! use tt_audio::AudioService;
//! use tt_audio::RodioPlayer;
//! use tt_core::EventBus;
//! use std::path::Path;
//!
//! // Создаём плеер и сервис
//! let player = RodioPlayer::new()?;
//! let event_bus = EventBus::new(100);
//! let audio_service = AudioService::new(player, event_bus);
//!
//! // Воспроизводим файл
//! audio_service.play(Path::new("/path/to/sound.mp3"), 0.0); // 0 дБ = нормальная громкость
//!
//! # Ok::<(), tt_audio::AudioError>(())
//! ```

mod error;
mod player;
mod service;
mod volume;

pub use error::AudioError;
pub use player::{AudioPlayer, RodioPlayer};
pub use service::AudioService;
pub use volume::{db_to_linear, linear_to_db};

/// Возвращает версию крейта
#[must_use]
pub fn version() -> &'static str {
    "0.1.0"
}
