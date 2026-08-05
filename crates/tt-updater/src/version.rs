//! Сравнение версий с использованием semver

use semver::Version;

use crate::UpdaterError;

/// Результат сравнения версий
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum VersionComparison {
    /// Первая версия старше второй
    Older,
    /// Версии равны
    Equal,
    /// Первая версия новее второй
    Newer,
}

/// Нормализует строку версии для сравнения
///
/// Удаляет префикс 'v' если он есть, затем парсит как semver.
///
/// # Примеры
///
/// ```
/// use tt_updater::normalize_version;
///
/// assert_eq!(normalize_version("v1.2.3").unwrap().to_string(), "1.2.3");
/// assert_eq!(normalize_version("1.2.3").unwrap().to_string(), "1.2.3");
/// ```
pub fn normalize_version(version_str: &str) -> Result<Version, UpdaterError> {
    // Удаляем префикс 'v' если есть (как в Python-версии: latest_version.lstrip('v'))
    let normalized = version_str.strip_prefix('v').unwrap_or(version_str);

    // Парсим как semver
    normalized
        .parse::<Version>()
        .map_err(|_| UpdaterError::InvalidVersion {
            version: version_str.to_string(),
        })
}

/// Сравнивает две версии
///
/// # Возвращает
///
/// - `VersionComparison::Older` — если `v1` старее `v2`
/// - `VersionComparison::Equal` — если версии равны
/// - `VersionComparison::Newer` — если `v1` новее `v2`
///
/// # Примеры
///
/// ```
/// use tt_updater::{compare_versions, normalize_version, VersionComparison};
///
/// let v1 = normalize_version("1.0.0").unwrap();
/// let v2 = normalize_version("2.0.0").unwrap();
/// assert_eq!(compare_versions(&v1, &v2), VersionComparison::Older);
///
/// let v1 = normalize_version("2.0.0").unwrap();
/// let v2 = normalize_version("1.0.0").unwrap();
/// assert_eq!(compare_versions(&v1, &v2), VersionComparison::Newer);
///
/// let v1 = normalize_version("1.0.0").unwrap();
/// let v2 = normalize_version("1.0.0").unwrap();
/// assert_eq!(compare_versions(&v1, &v2), VersionComparison::Equal);
/// ```
pub fn compare_versions(v1: &Version, v2: &Version) -> VersionComparison {
    use std::cmp::Ordering;

    match v1.cmp(v2) {
        Ordering::Less => VersionComparison::Older,
        Ordering::Equal => VersionComparison::Equal,
        Ordering::Greater => VersionComparison::Newer,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // ------------------------------------------------------------------------
    // Тесты нормализации версий
    // ------------------------------------------------------------------------

    #[test]
    fn test_normalize_version_with_v_prefix() {
        let result = normalize_version("v1.2.3").unwrap();
        assert_eq!(result.major, 1);
        assert_eq!(result.minor, 2);
        assert_eq!(result.patch, 3);
    }

    #[test]
    fn test_normalize_version_without_prefix() {
        let result = normalize_version("1.2.3").unwrap();
        assert_eq!(result.major, 1);
        assert_eq!(result.minor, 2);
        assert_eq!(result.patch, 3);
    }

    #[test]
    fn test_normalize_version_multiple_components() {
        // semver не поддерживает 4-ю компоненту, но это нормально
        // Версии типа "1.2.3.4" будут распарсены с ошибкой
        assert!(normalize_version("v1.2.3.4").is_err());
    }

    #[test]
    fn test_normalize_version_with_pre() {
        let result = normalize_version("v1.2.3-alpha").unwrap();
        assert_eq!(result.major, 1);
        assert_eq!(result.minor, 2);
        assert_eq!(result.patch, 3);
        // semver корректно обрабатывает prerelease теги
        assert!(!result.pre.is_empty());
    }

    #[test]
    fn test_normalize_version_invalid() {
        assert!(matches!(
            normalize_version("not-a-version"),
            Err(UpdaterError::InvalidVersion { .. })
        ));

        assert!(matches!(
            normalize_version(""),
            Err(UpdaterError::InvalidVersion { .. })
        ));

        assert!(matches!(
            normalize_version("v"),
            Err(UpdaterError::InvalidVersion { .. })
        ));

        assert!(matches!(
            normalize_version("1.2."),
            Err(UpdaterError::InvalidVersion { .. })
        ));
    }

    // ------------------------------------------------------------------------
    // Тесты сравнения версий
    // ------------------------------------------------------------------------

    #[test]
    fn test_compare_versions_older() {
        let v1 = normalize_version("1.0.0").unwrap();
        let v2 = normalize_version("2.0.0").unwrap();

        assert_eq!(compare_versions(&v1, &v2), VersionComparison::Older);
    }

    #[test]
    fn test_compare_versions_newer() {
        let v1 = normalize_version("2.0.0").unwrap();
        let v2 = normalize_version("1.0.0").unwrap();

        assert_eq!(compare_versions(&v1, &v2), VersionComparison::Newer);
    }

    #[test]
    fn test_compare_versions_equal() {
        let v1 = normalize_version("1.0.0").unwrap();
        let v2 = normalize_version("1.0.0").unwrap();

        assert_eq!(compare_versions(&v1, &v2), VersionComparison::Equal);
    }

    #[test]
    fn test_compare_versions_with_patch() {
        let v1 = normalize_version("1.0.0").unwrap();
        let v2 = normalize_version("1.0.1").unwrap();

        assert_eq!(compare_versions(&v1, &v2), VersionComparison::Older);
    }

    #[test]
    fn test_compare_versions_with_minor() {
        let v1 = normalize_version("1.0.0").unwrap();
        let v2 = normalize_version("1.1.0").unwrap();

        assert_eq!(compare_versions(&v1, &v2), VersionComparison::Older);
    }

    #[test]
    fn test_compare_versions_with_major() {
        let v1 = normalize_version("1.0.0").unwrap();
        let v2 = normalize_version("2.0.0").unwrap();

        assert_eq!(compare_versions(&v1, &v2), VersionComparison::Older);
    }

    #[test]
    fn test_compare_versions_newer_with_patch() {
        let v1 = normalize_version("1.0.1").unwrap();
        let v2 = normalize_version("1.0.0").unwrap();

        assert_eq!(compare_versions(&v1, &v2), VersionComparison::Newer);
    }

    #[test]
    fn test_compare_versions_with_v_prefix() {
        let v1 = normalize_version("v1.0.0").unwrap();
        let v2 = normalize_version("2.0.0").unwrap();

        assert_eq!(compare_versions(&v1, &v2), VersionComparison::Older);
    }

    #[test]
    fn test_compare_versions_both_with_v_prefix() {
        let v1 = normalize_version("v1.0.0").unwrap();
        let v2 = normalize_version("v2.0.0").unwrap();

        assert_eq!(compare_versions(&v1, &v2), VersionComparison::Older);
    }

    // ------------------------------------------------------------------------
    // Тесты на крайние случаи
    // ------------------------------------------------------------------------

    #[test]
    fn test_compare_versions_zero() {
        let v1 = normalize_version("0.0.1").unwrap();
        let v2 = normalize_version("0.0.2").unwrap();

        assert_eq!(compare_versions(&v1, &v2), VersionComparison::Older);
    }

    #[test]
    fn test_compare_versions_large_numbers() {
        let v1 = normalize_version("10.20.30").unwrap();
        let v2 = normalize_version("11.20.30").unwrap();

        assert_eq!(compare_versions(&v1, &v2), VersionComparison::Older);
    }

    #[test]
    fn test_installed_version_newer_than_release() {
        // Тест на случай, когда установленная версия новее релизной
        let installed = normalize_version("2.0.0").unwrap();
        let release = normalize_version("1.0.0").unwrap();

        assert_eq!(
            compare_versions(&installed, &release),
            VersionComparison::Newer
        );
    }
}
