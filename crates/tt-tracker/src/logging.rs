//! Настройка файлового логирования с суточной ротацией и ретенцией 7 дней

use std::fs;
use std::path::PathBuf;
use std::time::SystemTime;
use tracing_appender::rolling::{RollingFileAppender, Rotation};
use tracing_subscriber::{fmt, layer::SubscriberExt, util::SubscriberInitExt, EnvFilter};

/// Каталог для логов: ~/.time_tracker/logs/
pub fn logs_dir() -> PathBuf {
    let mut path = dirs::home_dir().expect("Не найден домашний каталог");
    path.push(".time_tracker");
    path.push("logs");
    path
}

/// Удаляет файлы логов старше 7 дней
///
/// Вызывается при старте приложения для очистки старых файлов.
pub fn cleanup_old_logs(log_dir: &PathBuf, retention_days: u64) {
    let now = SystemTime::now();

    if !log_dir.exists() {
        if let Err(e) = fs::create_dir_all(log_dir) {
            eprintln!("Не удалось создать каталог логов {:?}: {}", log_dir, e);
        }
        return;
    }

    let entries = match fs::read_dir(log_dir) {
        Ok(entries) => entries,
        Err(e) => {
            eprintln!("Не удалось прочитать каталог логов {:?}: {}", log_dir, e);
            return;
        }
    };

    for entry in entries.flatten() {
        let path = entry.path();

        // Удаляем только файлы, не каталоги
        if !path.is_file() {
            continue;
        }

        // Получаем время изменения файла
        let metadata = match fs::metadata(&path) {
            Ok(m) => m,
            Err(e) => {
                eprintln!("Не удалось получить метаданные {:?}: {}", path, e);
                continue;
            }
        };

        let modified = match metadata.modified() {
            Ok(t) => t,
            Err(e) => {
                eprintln!("Не удалось получить время изменения {:?}: {}", path, e);
                continue;
            }
        };

        // Вычисляем возраст файла
        let age = match now.duration_since(modified) {
            Ok(d) => d,
            Err(_) => {
                // Файл изменён в будущем — пропускаем
                continue;
            }
        };

        // Вычисляем возраст файла в секундах
        let age_seconds = age.as_secs();

        // Удаляем файлы старше retention_days полных дней
        // Файл возрастом ровно retention_days дней НЕ удаляется
        // (только если старше retention_days полных дней)
        if age_seconds > retention_days * 24 * 60 * 60 {
            if let Err(e) = fs::remove_file(&path) {
                eprintln!("Не удалось удалить старый файл логов {:?}: {}", path, e);
            } else {
                println!("Удалён старый файл логов: {:?}", path);
            }
        }
    }
}

/// Инициализирует файловое логирование с суточной ротацией
///
/// Логи пишутся в каталог ~/.time_tracker/logs/
/// Ротация — каждый день, ретенция — 7 дней (удаляются файлы старше 7 дней при старте)
pub fn init_logging() {
    let log_dir = logs_dir();

    // Создаём каталог для логов, если его нет
    if !log_dir.exists() {
        if let Err(e) = fs::create_dir_all(&log_dir) {
            eprintln!("Не удалось создать каталог логов {:?}: {}", log_dir, e);
        }
    }

    // Удаляем старые файлы логов (ретенция 7 дней)
    cleanup_old_logs(&log_dir, 7);

    // Создаём appender с суточной ротацией
    let file_appender = RollingFileAppender::new(Rotation::DAILY, &log_dir, "timetracker");

    // Настраиваем формат логов
    let env_filter = EnvFilter::from_default_env()
        .add_directive(tracing::Level::INFO.into())
        .add_directive("time_tracker=debug".parse().unwrap())
        .add_directive("tt_tracker=debug".parse().unwrap());

    tracing_subscriber::registry()
        .with(env_filter)
        .with(
            fmt::layer()
                .with_writer(file_appender)
                .with_ansi(false) // Нет ANSI-кодов в файле
                .with_target(true)
                .with_thread_ids(false)
                .with_thread_names(false)
                .with_file(false)
                .with_line_number(false),
        )
        .with(
            fmt::layer()
                .with_writer(std::io::stdout)
                .with_ansi(true)
                .with_target(true),
        )
        .init();
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs::{self, File};
    use std::io::Write;
    use std::path::{Path, PathBuf};
    use std::time::{Duration, SystemTime};
    use tempfile::TempDir;

    /// Создаёт тестовый файл логов с указанным возрастом
    fn create_test_file(dir: &Path, name: &str, age_seconds: u64) -> PathBuf {
        let path = dir.join(name);
        let mut file = File::create(&path).unwrap();
        writeln!(file, "test log content").unwrap();

        // Устанавливаем время модификации файла
        let now = std::time::SystemTime::now();
        let modified_time = now - std::time::Duration::from_secs(age_seconds);

        file.set_modified(modified_time).unwrap();

        path
    }

    fn create_test_file_at(dir: &Path, name: &str, modified_time: SystemTime) -> PathBuf {
        let path = dir.join(name);
        let mut file = File::create(&path).unwrap();
        writeln!(file, "test log content").unwrap();

        file.set_modified(modified_time).unwrap();

        path
    }

    #[test]
    fn test_cleanup_old_logs_removes_old_files() {
        let temp_dir = TempDir::new().unwrap();
        let log_dir = temp_dir.path().to_path_buf();

        // Создаём файлы разных возрастов
        let old_file = create_test_file(&log_dir, "old.log", 10 * 24 * 60 * 60); // 10 дней назад
        let recent_file = create_test_file(&log_dir, "recent.log", 3 * 24 * 60 * 60); // 3 дня назад
        let fresh_file = create_test_file(&log_dir, "fresh.log", 60 * 60); // 1 час назад

        // Запускаем очистку с ретенцией 7 дней
        cleanup_old_logs(&log_dir, 7);

        // Проверяем, что старый файл удалён
        assert!(!old_file.exists(), "Старый файл должен быть удалён");

        // Проверяем, что свежие файлы остались
        assert!(recent_file.exists(), "Свежий файл (3 дня) должен остаться");
        assert!(fresh_file.exists(), "Свежий файл (1 час) должен остаться");
    }

    #[test]
    fn test_cleanup_old_logs_keeps_exactly_7_days() {
        let temp_dir = TempDir::new().unwrap();
        let log_dir = temp_dir.path().to_path_buf();

        // Фиксируем текущее время для вычисления возрастов
        let now = std::time::SystemTime::now();

        // Создаём файлы вокруг границы ретенции, используя фиксированное время
        let six_days_file = create_test_file_at(
            &log_dir,
            "six_days.log",
            now - Duration::from_secs(6 * 24 * 60 * 60),
        ); // 6 дней назад
        let eight_days_file = create_test_file_at(
            &log_dir,
            "eight_days.log",
            now - Duration::from_secs(8 * 24 * 60 * 60),
        ); // 8 дней назад

        // Создаём семидневный файл в самом конце, чтобы его возраст был максимально близок к ровно 7 дням
        let seven_days_file = create_test_file_at(
            &log_dir,
            "seven_days.log",
            now - Duration::from_secs(7 * 24 * 60 * 60),
        ); // ровно 7 дней назад

        // Запускаем очистку с ретенцией 7 дней
        cleanup_old_logs(&log_dir, 7);

        // Проверяем, что файлы старше 7 дней удалены
        assert!(
            !eight_days_file.exists(),
            "Файл старше 7 дней должен быть удалён"
        );

        // Проверяем, что файлы 7 дней и новее остались
        assert!(
            seven_days_file.exists(),
            "Файл ровно 7 дней должен остаться"
        );
        assert!(six_days_file.exists(), "Файл 6 дней должен остаться");
    }

    #[test]
    fn test_cleanup_old_logs_skips_directories() {
        let temp_dir = TempDir::new().unwrap();
        let log_dir = temp_dir.path().to_path_buf();

        // Создаём подкаталог
        let subdir = log_dir.join("subdir");
        fs::create_dir(&subdir).unwrap();

        // Создаём старый файл в подкаталоге
        let old_file = create_test_file(&subdir, "old.log", 10 * 24 * 60 * 60);

        // Запускаем очистку
        cleanup_old_logs(&log_dir, 7);

        // Подкаталог и его содержимое должны остаться (удаляем только файлы в log_dir)
        assert!(subdir.exists(), "Подкаталог должен остаться");
        assert!(old_file.exists(), "Файл в подкаталоге должен остаться");
    }

    #[test]
    fn test_cleanup_old_logs_creates_directory_if_missing() {
        let temp_dir = TempDir::new().unwrap();
        let log_dir = temp_dir.path().join("nonexistent");

        assert!(!log_dir.exists(), "Каталог не должен существовать");

        // Запускаем очистку несуществующего каталога
        cleanup_old_logs(&log_dir, 7);

        // Каталог должен быть создан
        assert!(log_dir.exists(), "Каталог должен быть создан");
    }

    #[test]
    fn test_cleanup_old_logs_handles_future_modified_files() {
        let temp_dir = TempDir::new().unwrap();
        let log_dir = temp_dir.path().to_path_buf();

        // Создаём файл и устанавливаем время модификации в будущее
        let path = log_dir.join("future.log");
        let mut file = File::create(&path).unwrap();
        writeln!(file, "test log content").unwrap();

        let now = std::time::SystemTime::now();
        let future_time = now + std::time::Duration::from_secs(60 * 60); // +1 час
        file.set_modified(future_time).unwrap();

        // Запускаем очистку
        cleanup_old_logs(&log_dir, 7);

        // Файл в будущем должен остаться
        assert!(
            path.exists(),
            "Файл с будущим временем модификации должен остаться"
        );
    }
}
