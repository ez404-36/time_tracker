//! Конвертация громкости из децибел в линейный множитель

/// Конвертирует громкость из децибел (амплитудных) в линейный множитель
///
/// Формула: `linear = 10^(dB / 20)`
///
/// Это правильная формула для амплитудных децибел (как в pydub).
/// Не путать с `10^(dB/10)`, которая используется для мощности.
///
/// # Примеры
/// - 0 дБ = 1.0 (без изменения)
/// - -6 дБ ≈ 0.501 (половина громкости)
/// - +6 дБ ≈ 1.995 (удвоение громкости)
///
/// # Arguments
/// * `db` - громкость в децибелах (может быть отрицательной)
///
/// # Returns
/// Линейный множитель громкости (всегда положительный)
#[must_use]
pub fn db_to_linear(db: f32) -> f32 {
    10.0_f32.powf(db / 20.0)
}

/// Конвертирует линейный множитель громкости в децибелы
///
/// Обратная функция к `db_to_linear`.
///
/// # Arguments
/// * `linear` - линейный множитель громкости (должен быть положительным)
///
/// # Returns
/// Громкость в децибелах
///
/// # Panics
/// Паникует если `linear` <= 0
#[must_use]
pub fn linear_to_db(linear: f32) -> f32 {
    assert!(linear > 0.0, "Линейный множитель должен быть положительным");
    20.0 * linear.log10()
}

#[cfg(test)]
mod tests {
    use super::*;

    // ------------------------------------------------------------------------
    // Тесты конвертации дБ → линейный множитель
    // ------------------------------------------------------------------------

    #[test]
    fn test_db_zero() {
        let result = db_to_linear(0.0);
        assert!(
            (result - 1.0).abs() < 0.001,
            "0 дБ должен быть 1.0, получено {}",
            result
        );
    }

    #[test]
    fn test_db_negative_6() {
        let result = db_to_linear(-6.0);
        assert!(
            (result - 0.501).abs() < 0.001,
            "-6 дБ должен быть ~0.501, получено {}",
            result
        );
    }

    #[test]
    fn test_db_positive_6() {
        let result = db_to_linear(6.0);
        assert!(
            (result - 1.995).abs() < 0.001,
            "+6 дБ должен быть ~1.995, получено {}",
            result
        );
    }

    #[test]
    fn test_db_negative_infinity() {
        let result = db_to_linear(-1000.0);
        assert!(
            result < 0.001,
            "Очень отрицательные дБ должны давать почти 0, получено {}",
            result
        );
    }

    #[test]
    fn test_db_positive_loud() {
        let result = db_to_linear(20.0);
        assert!(
            (result - 10.0).abs() < 0.1,
            "+20 дБ должен быть ~10.0, получено {}",
            result
        );
    }

    #[test]
    fn test_db_symmetry() {
        // Конвертация туда-обратно должна быть симметричной
        for db in [-20.0, -10.0, -6.0, -3.0, 0.0, 3.0, 6.0, 10.0, 20.0] {
            let linear = db_to_linear(db);
            let restored = linear_to_db(linear);
            assert!(
                (restored - db).abs() < 0.1,
                "Туда-обратно для {db} дБ: {restored} дБ"
            );
        }
    }

    // ------------------------------------------------------------------------
    // Тесты обратной конвертации
    // ------------------------------------------------------------------------

    #[test]
    fn test_linear_to_db_half() {
        let result = linear_to_db(0.5);
        assert!(
            (result - (-6.02)).abs() < 0.1,
            "0.5 должно быть ~-6.02 дБ, получено {}",
            result
        );
    }

    #[test]
    fn test_linear_to_db_double() {
        let result = linear_to_db(2.0);
        assert!(
            (result - 6.02).abs() < 0.1,
            "2.0 должно быть ~6.02 дБ, получено {}",
            result
        );
    }

    #[test]
    #[should_panic]
    fn test_linear_to_db_zero_panics() {
        let _ = linear_to_db(0.0);
    }

    #[test]
    #[should_panic]
    fn test_linear_to_db_negative_panics() {
        let _ = linear_to_db(-1.0);
    }
}
