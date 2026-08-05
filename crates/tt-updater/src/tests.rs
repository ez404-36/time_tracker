//! Интеграционные тесты с wiremock

use super::*;
use tt_core::EventBus;
use wiremock::{
    matchers::{method, path},
    Mock, MockServer, ResponseTemplate,
};

fn create_parser() -> GitHubReleaseParser {
    GitHubReleaseParser::new(10)
}

// ============================================================================
// Юнит-тесты (без сети)
// ============================================================================

/// Проверка корректного извлечения параметров из URL
/// Аналог: test_extract_repo_params_success
#[test]
fn test_extract_repo_params_success() {
    let parser = create_parser();
    let url = "https://github.com/ez404-36/time_tracker/releases";

    let result = parser.extract_repo_info(url).unwrap();

    assert_eq!(result.owner, "ez404-36");
    assert_eq!(result.repo, "time_tracker");
}

/// Проверка обработки некорректного URL
#[test]
fn test_extract_repo_params_invalid_url() {
    let parser = create_parser();
    let url = "https://example.com/not-github/releases";

    let result = parser.extract_repo_info(url);

    assert!(matches!(result, Err(UpdaterError::InvalidUrl { .. })));
}

/// Проверка обработки URL с отсутствующим owner
#[test]
fn test_extract_repo_params_missing_owner() {
    let parser = create_parser();
    let url = "https://github.com//repo/releases";

    let result = parser.extract_repo_info(url);

    assert!(matches!(result, Err(UpdaterError::InvalidUrl { .. })));
}

/// Проверка логики извлечения разных вариаций URL
#[test]
fn test_extract_repo_various_urls() {
    let parser = create_parser();

    // Стандартный URL
    let result = parser
        .extract_repo_info("https://github.com/owner/repo/releases")
        .unwrap();
    assert_eq!(result.owner, "owner");
    assert_eq!(result.repo, "repo");

    // URL с дефисами в имени
    let result = parser
        .extract_repo_info("https://github.com/my-org/my-repo/releases")
        .unwrap();
    assert_eq!(result.owner, "my-org");
    assert_eq!(result.repo, "my-repo");

    // URL без /releases
    let result = parser
        .extract_repo_info("https://github.com/owner/repo")
        .unwrap();
    assert_eq!(result.owner, "owner");
    assert_eq!(result.repo, "repo");
}

/// Проверка формирования URL API
#[test]
fn test_api_url_formation() {
    let parser = create_parser();

    let repo_info = parser
        .extract_repo_info("https://github.com/ez404-36/time_tracker/releases")
        .unwrap();

    assert_eq!(repo_info.owner, "ez404-36");
    assert_eq!(repo_info.repo, "time_tracker");

    let api_path = API_PATH_TEMPLATE
        .replace("{owner}", &repo_info.owner)
        .replace("{repo}", &repo_info.repo);

    assert_eq!(api_path, "/repos/ez404-36/time_tracker/releases");
}

/// Проверка сравнения версий (установленная новее релизной)
#[tokio::test]
async fn test_installed_version_newer_than_release() {
    let current = normalize_version("2.0.0").unwrap();
    let latest = normalize_version("v1.0.0").unwrap();

    assert_eq!(
        compare_versions(&current, &latest),
        VersionComparison::Newer
    );
}

/// Проверка нормализации версий с разными префиксами
#[tokio::test]
async fn test_version_normalization_variations() {
    let v1 = normalize_version("v1.2.3").unwrap();
    let v2 = normalize_version("1.2.3").unwrap();

    assert_eq!(compare_versions(&v1, &v2), VersionComparison::Equal);
}

/// Проверка логики check_for_update при наличии обновления
#[tokio::test]
async fn test_check_for_update_logic() {
    let current = normalize_version("1.0.0").unwrap();
    let latest = normalize_version("v2.0.0").unwrap();

    assert_eq!(
        compare_versions(&current, &latest),
        VersionComparison::Older
    );
}

/// Проверка логики check_for_update при отсутствии обновления
#[tokio::test]
async fn test_check_for_update_not_available_logic() {
    let current = normalize_version("2.0.0").unwrap();
    let latest = normalize_version("v1.0.0").unwrap();

    assert_eq!(
        compare_versions(&current, &latest),
        VersionComparison::Newer
    );

    // Проверяем равные версии
    let current = normalize_version("1.0.0").unwrap();
    let latest = normalize_version("v1.0.0").unwrap();

    assert_eq!(
        compare_versions(&current, &latest),
        VersionComparison::Equal
    );
}

// ============================================================================
// Сетевые тесты с wiremock (без реального интернета)
// ============================================================================

/// Успешное получение тега последнего релиза
/// Аналог: test_get_latest_release_tag_success
#[tokio::test]
async fn test_get_latest_release_tag_success() {
    let mock_server = MockServer::start().await;

    Mock::given(method("GET"))
        .and(path("/repos/owner/repo/releases"))
        .respond_with(
            ResponseTemplate::new(200).set_body_json(vec![serde_json::json!({
                "tag_name": "v2.0.0"
            })]),
        )
        .mount(&mock_server)
        .await;

    let parser = GitHubReleaseParser::with_api_base_url(mock_server.uri(), 10);
    let event_bus = EventBus::new(10);

    // Для отладки
    eprintln!("Mock server URI: {}", mock_server.uri());

    let result = parser
        .get_latest_release_tag("https://github.com/owner/repo/releases", Some(&event_bus))
        .await;

    match &result {
        Ok(tag) => eprintln!("Got tag: {}", tag),
        Err(e) => eprintln!("Error: {:?}", e),
    }

    assert_eq!(result.unwrap(), "v2.0.0");

    drop(event_bus);
}

/// Проверка обработки ошибки 404
/// Аналог: test_get_latest_release_404
#[tokio::test]
async fn test_get_latest_release_404() {
    let mock_server = MockServer::start().await;

    Mock::given(method("GET"))
        .respond_with(ResponseTemplate::new(404))
        .mount(&mock_server)
        .await;

    let parser = GitHubReleaseParser::with_api_base_url(mock_server.uri(), 10);
    let event_bus = EventBus::new(10);
    let mut rx = event_bus.subscribe();

    let result = parser
        .get_latest_release_tag("https://github.com/owner/repo/releases", Some(&event_bus))
        .await;

    assert!(matches!(result, Err(UpdaterError::NotFound)));

    // Проверяем, что ошибка была опубликована в шину событий
    let received = rx.recv().await;
    assert!(received.is_ok());

    if let Ok(SystemEvent::ErrorSystem { source, error }) = received {
        assert_eq!(source, "tt-updater");
        assert!(error.contains("404"));
    } else {
        panic!("Expected ErrorSystem event");
    }

    drop(rx);
    drop(event_bus);
}

/// Проверка ситуации с пустым списком релизов
/// Аналог: test_get_latest_release_empty
#[tokio::test]
async fn test_get_latest_release_empty() {
    let mock_server = MockServer::start().await;

    Mock::given(method("GET"))
        .respond_with(ResponseTemplate::new(200).set_body_json::<Vec<serde_json::Value>>(vec![]))
        .mount(&mock_server)
        .await;

    let parser = GitHubReleaseParser::with_api_base_url(mock_server.uri(), 10);
    let event_bus = EventBus::new(10);
    let mut rx = event_bus.subscribe();

    let result = parser
        .get_latest_release_tag("https://github.com/owner/repo/releases", Some(&event_bus))
        .await;

    assert!(matches!(result, Err(UpdaterError::NoReleases)));

    // Проверяем, что ошибка была опубликована в шину событий
    let received = rx.recv().await;
    assert!(received.is_ok());

    if let Ok(SystemEvent::ErrorSystem { source, error }) = received {
        assert_eq!(source, "tt-updater");
        assert!(error.contains("пуст"));
    } else {
        panic!("Expected ErrorSystem event");
    }

    drop(rx);
    drop(event_bus);
}

/// Проверка обработки сетевой ошибки (ClientError)
/// Аналог: test_network_failure
#[tokio::test]
async fn test_network_failure() {
    let event_bus = EventBus::new(10);
    let mut rx = event_bus.subscribe();

    // Для тестирования реальной сетевой ошибки используем недоступный хост
    let parser_with_bad_url = GitHubReleaseParser::with_api_base_url(
        "http://this-host-does-not-exist-12345.local".to_string(),
        1, // короткий таймаут
    );

    let result = parser_with_bad_url
        .get_latest_release_tag("https://github.com/owner/repo/releases", Some(&event_bus))
        .await;

    // Проверяем, что вернулась ошибка сети
    assert!(matches!(result, Err(UpdaterError::NetworkError { .. })));

    // Проверяем, что ошибка была опубликована в шину событий
    let received = rx.recv().await;
    assert!(received.is_ok());

    if let Ok(SystemEvent::ErrorSystem { source, error }) = received {
        assert_eq!(source, "tt-updater");
        assert!(error.contains("сетев") || error.contains("запрос"));
    } else {
        panic!("Expected ErrorSystem event");
    }

    drop(rx);
    drop(event_bus);
}

/// Проверка обработки некорректного JSON
#[tokio::test]
async fn test_invalid_json() {
    let mock_server = MockServer::start().await;

    Mock::given(method("GET"))
        .respond_with(ResponseTemplate::new(200).set_body_string("not valid json"))
        .mount(&mock_server)
        .await;

    let parser = GitHubReleaseParser::with_api_base_url(mock_server.uri(), 10);
    let event_bus = EventBus::new(10);
    let mut rx = event_bus.subscribe();

    let result = parser
        .get_latest_release_tag("https://github.com/owner/repo/releases", Some(&event_bus))
        .await;

    assert!(matches!(result, Err(UpdaterError::ParseError { .. })));

    // Проверяем, что ошибка была опубликована в шину событий
    let received = rx.recv().await;
    assert!(received.is_ok());

    if let Ok(SystemEvent::ErrorSystem { source, error }) = received {
        assert_eq!(source, "tt-updater");
        assert!(error.contains("парсинг") || error.contains("JSON"));
    } else {
        panic!("Expected ErrorSystem event");
    }

    drop(rx);
    drop(event_bus);
}

/// Проверка обработки rate limit (403 с X-RateLimit-Remaining: 0)
#[tokio::test]
async fn test_rate_limit_exceeded() {
    let mock_server = MockServer::start().await;

    Mock::given(method("GET"))
        .respond_with(ResponseTemplate::new(403).insert_header("X-RateLimit-Remaining", "0"))
        .mount(&mock_server)
        .await;

    let parser = GitHubReleaseParser::with_api_base_url(mock_server.uri(), 10);
    let event_bus = EventBus::new(10);
    let mut rx = event_bus.subscribe();

    let result = parser
        .get_latest_release_tag("https://github.com/owner/repo/releases", Some(&event_bus))
        .await;

    assert!(matches!(result, Err(UpdaterError::RateLimitExceeded)));

    // Проверяем, что ошибка была опубликована в шину событий
    let received = rx.recv().await;
    assert!(received.is_ok());

    if let Ok(SystemEvent::ErrorSystem { source, error }) = received {
        assert_eq!(source, "tt-updater");
        assert!(error.contains("rate limit") || error.contains("лимит"));
    } else {
        panic!("Expected ErrorSystem event");
    }

    drop(rx);
    drop(event_bus);
}

/// Проверка обработки 403 без rate limit (другая причина)
#[tokio::test]
async fn test_forbidden_without_rate_limit() {
    let mock_server = MockServer::start().await;

    Mock::given(method("GET"))
        .respond_with(ResponseTemplate::new(403).insert_header("X-RateLimit-Remaining", "60"))
        .mount(&mock_server)
        .await;

    let parser = GitHubReleaseParser::with_api_base_url(mock_server.uri(), 10);
    let event_bus = EventBus::new(10);

    let result = parser
        .get_latest_release_tag("https://github.com/owner/repo/releases", Some(&event_bus))
        .await;

    // Должен вернуть NetworkError, а не RateLimitExceeded
    assert!(matches!(result, Err(UpdaterError::NetworkError { .. })));

    drop(event_bus);
}

/// Проверка обработки неожиданного статуса ответа
#[tokio::test]
async fn test_unexpected_status() {
    let mock_server = MockServer::start().await;

    Mock::given(method("GET"))
        .respond_with(ResponseTemplate::new(500))
        .mount(&mock_server)
        .await;

    let parser = GitHubReleaseParser::with_api_base_url(mock_server.uri(), 10);
    let event_bus = EventBus::new(10);

    let result = parser
        .get_latest_release_tag("https://github.com/owner/repo/releases", Some(&event_bus))
        .await;

    assert!(matches!(result, Err(UpdaterError::NetworkError { .. })));

    drop(event_bus);
}

/// Проверка check_for_update при наличии обновления
#[tokio::test]
async fn test_check_for_update_available() {
    let mock_server = MockServer::start().await;

    Mock::given(method("GET"))
        .respond_with(
            ResponseTemplate::new(200).set_body_json(vec![serde_json::json!({
                "tag_name": "v2.0.0"
            })]),
        )
        .mount(&mock_server)
        .await;

    let parser = GitHubReleaseParser::with_api_base_url(mock_server.uri(), 10);
    let event_bus = EventBus::new(10);

    let result = parser
        .check_for_update(
            "1.0.0",
            "https://github.com/owner/repo/releases",
            Some(&event_bus),
        )
        .await;

    assert_eq!(result.unwrap(), Some("v2.0.0".to_string()));

    drop(event_bus);
}

/// Проверка check_for_update при отсутствии обновления
#[tokio::test]
async fn test_check_for_update_not_available() {
    let mock_server = MockServer::start().await;

    Mock::given(method("GET"))
        .respond_with(
            ResponseTemplate::new(200).set_body_json(vec![serde_json::json!({
                "tag_name": "v1.0.0"
            })]),
        )
        .mount(&mock_server)
        .await;

    let parser = GitHubReleaseParser::with_api_base_url(mock_server.uri(), 10);
    let event_bus = EventBus::new(10);

    let result = parser
        .check_for_update(
            "1.0.0",
            "https://github.com/owner/repo/releases",
            Some(&event_bus),
        )
        .await;

    assert_eq!(result.unwrap(), None);

    drop(event_bus);
}

/// Проверка check_for_update когда установленная версия новее релизной
#[tokio::test]
async fn test_check_for_update_installed_newer() {
    let mock_server = MockServer::start().await;

    Mock::given(method("GET"))
        .respond_with(
            ResponseTemplate::new(200).set_body_json(vec![serde_json::json!({
                "tag_name": "v1.0.0"
            })]),
        )
        .mount(&mock_server)
        .await;

    let parser = GitHubReleaseParser::with_api_base_url(mock_server.uri(), 10);
    let event_bus = EventBus::new(10);

    let result = parser
        .check_for_update(
            "2.0.0",
            "https://github.com/owner/repo/releases",
            Some(&event_bus),
        )
        .await;

    assert_eq!(result.unwrap(), None);

    drop(event_bus);
}

/// Проверка check_for_update при сетевой ошибке (возвращает Ok(None))
#[tokio::test]
async fn test_check_for_update_network_error() {
    let parser_with_bad_url = GitHubReleaseParser::with_api_base_url(
        "http://this-host-does-not-exist-12345.local".to_string(),
        1, // короткий таймаут
    );
    let event_bus = EventBus::new(10);

    let result = parser_with_bad_url
        .check_for_update(
            "1.0.0",
            "https://github.com/owner/repo/releases",
            Some(&event_bus),
        )
        .await;

    // Должен вернуть Ok(None) при сетевой ошибке
    assert!(matches!(result, Ok(None)));

    drop(event_bus);
}

/// Проверка check_for_update при rate limit (возвращает Ok(None))
#[tokio::test]
async fn test_check_for_update_rate_limit() {
    let mock_server = MockServer::start().await;

    Mock::given(method("GET"))
        .respond_with(ResponseTemplate::new(403).insert_header("X-RateLimit-Remaining", "0"))
        .mount(&mock_server)
        .await;

    let parser = GitHubReleaseParser::with_api_base_url(mock_server.uri(), 10);
    let event_bus = EventBus::new(10);

    let result = parser
        .check_for_update(
            "1.0.0",
            "https://github.com/owner/repo/releases",
            Some(&event_bus),
        )
        .await;

    // Должен вернуть Ok(None) при rate limit
    assert!(matches!(result, Ok(None)));

    drop(event_bus);
}

/// Проверка check_for_update при некорректном URL (возвращает Err)
#[tokio::test]
async fn test_check_for_update_invalid_url() {
    let event_bus = EventBus::new(10);

    let parser = create_parser();

    // При некорректном URL должен возвращать Err (критическая ошибка)
    let result = parser
        .check_for_update("1.0.0", "https://example.com/not-github", Some(&event_bus))
        .await;

    assert!(matches!(result, Err(UpdaterError::InvalidUrl { .. })));

    drop(event_bus);
}

/// Проверка check_for_update при 404 (возвращает Err)
#[tokio::test]
async fn test_check_for_update_not_found() {
    let mock_server = MockServer::start().await;

    Mock::given(method("GET"))
        .respond_with(ResponseTemplate::new(404))
        .mount(&mock_server)
        .await;

    let parser = GitHubReleaseParser::with_api_base_url(mock_server.uri(), 10);
    let event_bus = EventBus::new(10);

    let result = parser
        .check_for_update(
            "1.0.0",
            "https://github.com/owner/repo/releases",
            Some(&event_bus),
        )
        .await;

    // Должен вернуть Err для NotFound (критическая ошибка)
    assert!(matches!(result, Err(UpdaterError::NotFound)));

    drop(event_bus);
}
