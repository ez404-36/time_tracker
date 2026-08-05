//! Типы ошибок аудио-крейта

use std::io;
use std::path::PathBuf;
use thiserror::Error;

/// Ошибки воспроизведения аудио
#[derive(Error, Debug)]
pub enum AudioError {
    /// Файл не найден
    #[error("Файл не найден: {path}")]
    FileNotFound { path: PathBuf },

    /// Формат файла не поддерживается
    #[error("Формат файла не поддерживается: {format}")]
    UnsupportedFormat { format: String },

    /// Ошибка чтения файла
    #[error("Ошибка чтения файла: {path} - {source}")]
    IoError {
        path: PathBuf,
        #[source]
        source: io::Error,
    },

    /// Ошибка инициализации аудиоустройства
    #[error("Ошибка инициализации аудиоустройства: {0}")]
    DeviceError(String),

    /// Ошибка декодирования аудио
    #[error("Ошибка декодирования аудио: {0}")]
    DecodeError(String),

    /// Аудиоустройство недоступно
    #[error("Аудиоустройство недоступно")]
    DeviceUnavailable,
}

impl From<rodio::decoder::DecoderError> for AudioError {
    fn from(err: rodio::decoder::DecoderError) -> Self {
        match err {
            rodio::decoder::DecoderError::UnrecognizedFormat => AudioError::UnsupportedFormat {
                format: "неизвестный".to_string(),
            },
            rodio::decoder::DecoderError::IoError(e) => AudioError::DecodeError(e.to_string()),
            _ => AudioError::DecodeError(err.to_string()),
        }
    }
}
