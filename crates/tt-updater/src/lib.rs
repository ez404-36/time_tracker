//! tt-updater: проверка релизов на GitHub (reqwest + semver).
//!
//! Этап 5.
//!
//! ## Функционал
//!
//! - Получение информации о последних релизах через GitHub API
//! - Сравнение версий с использованием `semver`
//! - Обработка сетевых ошибок и rate limit
//! - Публикация ошибок в шину событий `tt-core`
//!
//! ## Пример использования
//!
//! ```no_run
//! use tt_updater::GitHubReleaseParser;
//!
//! # async fn example() -> Result<(), Box<dyn std::error::Error>> {
//! let parser = GitHubReleaseParser::new(10);
//! let tag = parser.get_latest_release_tag("https://github.com/owner/repo/releases", None).await?;
//! # Ok(())
//! # }
//! ```
//!
//! ## Обработка ошибок
//!
//! Все ошибки публикуются как `SystemEvent::ErrorSystem` в шину событий.
//! Недоступность сети не приводит к падению приложения — ошибки логируются
//! и продолжают работу.

mod error;
mod version;

pub use error::UpdaterError;
pub use version::{compare_versions, normalize_version, VersionComparison};

use regex::Regex;
use reqwest::Client;
use serde::Deserialize;
use std::time::Duration;
use tracing::warn;
use tt_core::{EventBus, SystemEvent};

/// Базовый URL GitHub API по умолчанию
const DEFAULT_API_BASE_URL: &str = "https://api.github.com";

/// Шаблон URL для получения релизов (для формирования полного URL)
const API_PATH_TEMPLATE: &str = "/repos/{owner}/{repo}/releases";

/// Паттерн для извлечения owner и repo из URL GitHub
const URL_PATTERN: &str = r"github\.com/(?P<owner>[\w-]+)/(?P<repo>[\w-]+)";

/// Информация о репозитории GitHub
#[derive(Debug, Clone)]
struct RepoInfo {
    owner: String,
    repo: String,
}

/// Ответ GitHub API для релиза
#[derive(Debug, Deserialize)]
struct GitHubRelease {
    tag_name: String,
}

/// Парсер релизов GitHub
///
/// Использует официальный REST API GitHub, что обеспечивает стабильность
/// в отличие от классического веб-скрейпинга.
///
/// Базовый URL API можно переопределить для тестирования.
#[derive(Debug, Clone)]
pub struct GitHubReleaseParser {
    client: Client,
    url_regex: Regex,
    api_base_url: String,
}

impl GitHubReleaseParser {
    /// Создаёт новый парсер с указанным таймаутом
    ///
    /// # Параметры
    ///
    /// * `timeout_seconds` — максимальное время ожидания ответа от сервера в секундах
    ///
    /// # Пример
    ///
    /// ```
    /// use tt_updater::GitHubReleaseParser;
    ///
    /// let parser = GitHubReleaseParser::new(10);
    /// ```
    pub fn new(timeout_seconds: u64) -> Self {
        Self::with_api_base_url(DEFAULT_API_BASE_URL.to_string(), timeout_seconds)
    }

    /// Создаёт новый парсер с указанным базовым URL API и таймаутом
    ///
    /// # Параметры
    ///
    /// * `api_base_url` — базовый URL API (например, `"https://api.github.com"`)
    /// * `timeout_seconds` — максимальное время ожидания ответа от сервера в секундах
    ///
    /// # Пример
    ///
    /// ```
    /// use tt_updater::GitHubReleaseParser;
    ///
    /// let parser = GitHubReleaseParser::with_api_base_url("https://api.github.com".to_string(), 10);
    /// ```
    pub fn with_api_base_url(api_base_url: String, timeout_seconds: u64) -> Self {
        let client = Client::builder()
            .timeout(Duration::from_secs(timeout_seconds))
            .user_agent("TimeTracker/0.1.0 (https://github.com/egor/timetracker)")
            .build()
            .expect("Failed to create HTTP client");

        let url_regex = Regex::new(URL_PATTERN).expect("Invalid URL pattern regex");

        Self {
            client,
            url_regex,
            api_base_url,
        }
    }

    /// Извлекает owner и repo из URL GitHub
    ///
    /// # Параметры
    ///
    /// * `url` — полная ссылка на страницу релиза или репозитория
    ///
    /// # Возвращает
    ///
    /// `RepoInfo` с полями `owner` и `repo`
    ///
    /// # Ошибки
    ///
    /// Возвращает `UpdaterError::InvalidUrl` если URL не соответствует формату GitHub
    fn extract_repo_info(&self, url: &str) -> Result<RepoInfo, UpdaterError> {
        let captures = self
            .url_regex
            .captures(url)
            .ok_or_else(|| UpdaterError::InvalidUrl {
                url: url.to_string(),
            })?;

        let owner = captures
            .name("owner")
            .ok_or_else(|| UpdaterError::InvalidUrl {
                url: url.to_string(),
            })?
            .as_str()
            .to_string();

        let repo = captures
            .name("repo")
            .ok_or_else(|| UpdaterError::InvalidUrl {
                url: url.to_string(),
            })?
            .as_str()
            .to_string();

        Ok(RepoInfo { owner, repo })
    }

    /// Получает тег (версию) последнего релиза
    ///
    /// # Параметры
    ///
    /// * `github_url` — ссылка на страницу релизов GitHub
    /// * `event_bus` — опциональная шина событий для публикации ошибок
    ///
    /// # Возвращает
    ///
    /// Строку с названием тега (например, `'v1.0.0'`)
    ///
    /// # Ошибки
    ///
    /// - `UpdaterError::InvalidUrl` — некорректный URL
    /// - `UpdaterError::NetworkError` — ошибка сетевого запроса (включая rate limit)
    /// - `UpdaterError::ParseError` — ошибка парсинга JSON-ответа
    /// - `UpdaterError::NoReleases` — список релизов пуст
    /// - `UpdaterError::NotFound` — репозиторий или релизы не найдены (404)
    ///
    /// # Пример
    ///
    /// ```no_run
    /// # use tt_updater::GitHubReleaseParser;
    /// # async fn example() -> Result<(), Box<dyn std::error::Error>> {
    /// # let parser = GitHubReleaseParser::new(10);
    /// let tag = parser
    ///     .get_latest_release_tag("https://github.com/owner/repo/releases", None)
    ///     .await?;
    /// # Ok(())
    /// # }
    /// ```
    pub async fn get_latest_release_tag(
        &self,
        github_url: &str,
        event_bus: Option<&EventBus>,
    ) -> Result<String, UpdaterError> {
        let repo_info = self.extract_repo_info(github_url)?;
        let api_path = API_PATH_TEMPLATE
            .replace("{owner}", &repo_info.owner)
            .replace("{repo}", &repo_info.repo);
        let api_url = format!("{}{}", self.api_base_url, api_path);

        let response = self.client.get(&api_url).send().await.map_err(|e| {
            // Логируем сетевую ошибку, но не публикуем как событие
            // (это фоновая проверка, не должна ронять приложение)
            warn!("Ошибка сетевого запроса к GitHub API: {}", e);

            // Публикуем ошибку в шину событий, если она доступна
            if let Some(bus) = event_bus {
                bus.publish(SystemEvent::ErrorSystem {
                    source: "tt-updater".to_string(),
                    error: format!("Ошибка сетевого запроса к GitHub API: {}", e),
                });
            }

            UpdaterError::NetworkError {
                message: e.to_string(),
            }
        })?;

        let status = response.status();

        // Проверка rate limit (403 с X-RateLimit-Remaining: 0)
        if status.as_u16() == 403 {
            let rate_limit_remaining = response
                .headers()
                .get("X-RateLimit-Remaining")
                .and_then(|v| v.to_str().ok())
                .and_then(|s| s.parse::<u32>().ok());

            if rate_limit_remaining == Some(0) {
                warn!("GitHub API rate limit exceeded");

                if let Some(bus) = event_bus {
                    bus.publish(SystemEvent::ErrorSystem {
                        source: "tt-updater".to_string(),
                        error: "GitHub API rate limit exceeded".to_string(),
                    });
                }

                return Err(UpdaterError::RateLimitExceeded);
            }
        }

        if status.as_u16() == 404 {
            let error_msg = "Репозиторий или релизы не найдены (404).".to_string();

            if let Some(bus) = event_bus {
                bus.publish(SystemEvent::ErrorSystem {
                    source: "tt-updater".to_string(),
                    error: error_msg.clone(),
                });
            }

            return Err(UpdaterError::NotFound);
        }

        if !status.is_success() {
            let error_msg = format!(
                "GitHub API вернул статус {}: {}",
                status.as_u16(),
                status.canonical_reason().unwrap_or("Unknown")
            );

            if let Some(bus) = event_bus {
                bus.publish(SystemEvent::ErrorSystem {
                    source: "tt-updater".to_string(),
                    error: error_msg.clone(),
                });
            }

            return Err(UpdaterError::NetworkError { message: error_msg });
        }

        let releases: Vec<GitHubRelease> = response.json().await.map_err(|e| {
            let error_msg = format!("Ошибка парсинга JSON-ответа: {}", e);

            if let Some(bus) = event_bus {
                bus.publish(SystemEvent::ErrorSystem {
                    source: "tt-updater".to_string(),
                    error: error_msg.clone(),
                });
            }

            UpdaterError::ParseError { message: error_msg }
        })?;

        if releases.is_empty() {
            let error_msg = "Список релизов пуст.".to_string();

            if let Some(bus) = event_bus {
                bus.publish(SystemEvent::ErrorSystem {
                    source: "tt-updater".to_string(),
                    error: error_msg.clone(),
                });
            }

            return Err(UpdaterError::NoReleases);
        }

        // Первый элемент в списке 'releases' — это самый свежий релиз
        Ok(releases[0].tag_name.clone())
    }

    /// Проверяет, доступна ли новая версия приложения
    ///
    /// # Параметры
    ///
    /// * `current_version` — текущая версия приложения (например, `'0.1.0'`)
    /// * `github_url` — ссылка на страницу релизов GitHub
    /// * `event_bus` — опциональная шина событий для публикации ошибок
    ///
    /// # Возвращает
    ///
    /// `Ok(Some(tag))` — доступна новая версия, возвращает тег релиза
    /// `Ok(None)` — новая версия недоступна или ошибка сети
    /// `Err(_)` — критическая ошибка (например, неверный URL)
    ///
    /// # Пример
    ///
    /// ```no_run
    /// # use tt_updater::GitHubReleaseParser;
    /// # async fn example() -> Result<(), Box<dyn std::error::Error>> {
    /// # let parser = GitHubReleaseParser::new(10);
    /// match parser.check_for_update("0.1.0", "https://github.com/owner/repo/releases", None).await {
    ///     Ok(Some(tag)) => println!("Доступна новая версия: {}", tag),
    ///     Ok(None) => println!("Обновлений нет"),
    ///     Err(e) => eprintln!("Ошибка проверки обновлений: {}", e),
    /// }
    /// # Ok(())
    /// # }
    /// ```
    pub async fn check_for_update(
        &self,
        current_version: &str,
        github_url: &str,
        event_bus: Option<&EventBus>,
    ) -> Result<Option<String>, UpdaterError> {
        // Пытаемся получить последний релиз
        let latest_tag = match self.get_latest_release_tag(github_url, event_bus).await {
            Ok(tag) => tag,
            Err(UpdaterError::NetworkError { .. } | UpdaterError::RateLimitExceeded) => {
                // При сетевых ошибках или rate limit просто возвращаем None
                // (это фоновая проверка, не должна блокировать работу)
                warn!("Не удалось проверить обновления из-за ошибки сети или rate limit");
                return Ok(None);
            }
            Err(e) => return Err(e),
        };

        // Нормализуем версии
        let current = match normalize_version(current_version) {
            Ok(v) => v,
            Err(e) => {
                warn!("Некорректная текущая версия '{}': {}", current_version, e);
                return Ok(None);
            }
        };

        let latest = match normalize_version(&latest_tag) {
            Ok(v) => v,
            Err(e) => {
                warn!("Некорректная версия релиза '{}': {}", latest_tag, e);
                return Ok(None);
            }
        };

        // Сравниваем версии
        match compare_versions(&current, &latest) {
            VersionComparison::Older => Ok(Some(latest_tag)),
            VersionComparison::Equal | VersionComparison::Newer => Ok(None),
        }
    }
}

impl Default for GitHubReleaseParser {
    fn default() -> Self {
        Self::new(10)
    }
}

// ============================================================================
// Тесты
// ============================================================================

#[cfg(test)]
mod tests;
