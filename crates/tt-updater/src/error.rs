//! Ошибки крейта tt-updater

use thiserror::Error;

/// Ошибки парсера релизов GitHub
///
/// Аналог Python-исключения `GitHubReleaseError`.
/// Все сообщения об ошибках на русском языке, как в Python-версии.
#[derive(Debug, Error)]
pub enum UpdaterError {
    /// Некорректный URL
    #[error("Некорректный URL: {url}")]
    InvalidUrl { url: String },

    /// Ошибка сетевого запроса
    #[error("Ошибка сетевого запроса: {message}")]
    NetworkError { message: String },

    /// Ошибка парсинга JSON-ответа
    #[error("Ошибка парсинга JSON-ответа: {message}")]
    ParseError { message: String },

    /// Список релизов пуст
    #[error("Список релизов пуст.")]
    NoReleases,

    /// Репозиторий или релизы не найдены (404)
    #[error("Репозиторий или релизы не найдены (404).")]
    NotFound,

    /// Превышен rate limit GitHub API
    #[error("Превышен лимит запросов к GitHub API.")]
    RateLimitExceeded,

    /// Некорректная версия
    #[error("Некорректная версия: {version}")]
    InvalidVersion { version: String },
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_error_messages_are_russian() {
        let err = UpdaterError::InvalidUrl {
            url: "https://example.com".to_string(),
        };
        assert!(err.to_string().contains("Некорректный URL"));

        let err = UpdaterError::NetworkError {
            message: "Connection refused".to_string(),
        };
        assert!(err.to_string().contains("Ошибка сетевого запроса"));

        let err = UpdaterError::ParseError {
            message: "Invalid JSON".to_string(),
        };
        assert!(err.to_string().contains("Ошибка парсинга JSON-ответа"));

        let err = UpdaterError::NoReleases;
        assert!(err.to_string().contains("Список релизов пуст"));

        let err = UpdaterError::NotFound;
        assert!(err.to_string().contains("не найдены (404)"));

        let err = UpdaterError::RateLimitExceeded;
        assert!(err.to_string().contains("Превышен лимит запросов"));

        let err = UpdaterError::InvalidVersion {
            version: "abc".to_string(),
        };
        assert!(err.to_string().contains("Некорректная версия"));
    }
}
