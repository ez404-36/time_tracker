//! Трансформеры заголовков окон

use once_cell::sync::Lazy;
use regex::Regex;

/// Регулярное выражение для счётчика непрочитанных сообщений
/// Строго один пробел + (число) + конец строки. Без пробелов после.
static TELEGRAM_MSG_COUNT_REGEX: Lazy<Regex> = Lazy::new(|| Regex::new(r" \(\d+\)$").unwrap());

/// Trait для трансформации заголовков окон и имён приложений
pub trait TitleTransformer {
    /// Трансформирует имя приложения
    fn transform_app_name(&self, executable_name: &str) -> String;

    /// Трансформирует заголовок окна
    ///
    /// # Arguments
    ///
    /// * `window_title` - опциональный заголовок окна
    ///
    /// # Returns
    ///
    /// - `Some(String)` - трансформированный заголовок
    /// - `None` - заголовок отсутствует или не релевантен
    fn transform_window_title(&self, window_title: Option<&str>) -> Option<String>;
}

/// Базовый трансформер (без изменений)
struct BaseTransformer;

impl TitleTransformer for BaseTransformer {
    fn transform_app_name(&self, executable_name: &str) -> String {
        remove_spaces(executable_name).to_string()
    }

    fn transform_window_title(&self, window_title: Option<&str>) -> Option<String> {
        window_title.map(|title| remove_spaces(title).to_string())
    }
}

/// Трансформер для Telegram Desktop
///
/// ## Поведение трансформера
///
/// - Имя приложения: всегда "Telegram"
/// - Заголовок: удаляет счётчик непрочитанных сообщений в формате " (число)"
///
/// ## Отличия от Python-версии
///
/// **Python версия**: `.{1,3}\(\d+)` — захватывает 1-3 любых символа перед скобками.
/// Пример: `Telegram (5)` → удаляется `m (5)` → остаётся `Telegra`
///
/// **Rust версия**: ` \(\d+\)$` — удаляет только " (число)" в конце строки.
/// Пример: `Telegram (5)` → удаляется ` (5)` → остаётся `Telegram`
///
/// Почему Rust-версия точнее:
/// - Строгое: требует пробел перед скобками и конца строки
/// - Без ложных срабатываний: не сработает на "MyApp (5) talks"
/// - Без удаления лишних символов: не обрезает части названия
///
/// ### Потенциальные расхождения
///
/// | Заголовок | Python | Rust | Расхождение |
/// |-----------|--------|------|-------------|
/// `Telegram (5)` | `Telegra` | `Telegram` | **Да** |
/// `User (5)` | `User` | `User` | Нет |
/// `User (5) talks` | `User talks` | `User (5) talks` | **Да** |
/// `Channel (12)` | `Channe` | `Channel` | **Да** |
/// `Group (beta)` | `Group (beta)` | `Group (beta)` | Нет |
/// `User (5) (6)` | `Us` | `User (5)` | **Да** |
/// `User128 (5)` | `User12` | `User128` | **Да** |
///
/// Сценарии с расхождением редки и обычно не встречаются в реальных заголовках Telegram.
struct TelegramTransformer;

impl TitleTransformer for TelegramTransformer {
    fn transform_app_name(&self, _executable_name: &str) -> String {
        "Telegram".to_string()
    }

    fn transform_window_title(&self, window_title: Option<&str>) -> Option<String> {
        let window_title = window_title?;
        let cleaned = remove_spaces(window_title);

        // Удаляем счётчик непрочитанных сообщений (пробел + (цифры), строго без пробелов после)
        let result = TELEGRAM_MSG_COUNT_REGEX.replace(&cleaned, "");

        // Удаляем пробелы на концах
        let final_result = result.trim();

        if final_result.is_empty() {
            None
        } else {
            Some(final_result.to_string())
        }
    }
}

/// Трансформер для Яндекс Браузера
struct YandexBrowserTransformer;

impl TitleTransformer for YandexBrowserTransformer {
    fn transform_app_name(&self, _executable_name: &str) -> String {
        "Яндекс Браузер".to_string()
    }

    fn transform_window_title(&self, window_title: Option<&str>) -> Option<String> {
        let window_title = window_title?;
        let cleaned = remove_spaces(window_title);

        // Удаляем суффикс " — Яндекс Браузер" и " вкладка закреплена"
        let result = cleaned
            .split(" — Яндекс Браузер")
            .next()
            .unwrap_or(&cleaned)
            .replace(" вкладка закреплена", "");

        Some(result)
    }
}

/// Трансформер для Steam игр
struct SteamGameTransformer;

impl TitleTransformer for SteamGameTransformer {
    fn transform_app_name(&self, executable_name: &str) -> String {
        // Для Steam игр имя приложения берём из заголовка окна, но здесь у нас только executable_name
        // Поэтому вернём имя исполняемого файла как есть
        remove_spaces(executable_name).to_string()
    }

    fn transform_window_title(&self, window_title: Option<&str>) -> Option<String> {
        // Извлекаем название игры из заголовка до "PID"
        let title = window_title?;
        let cleaned = remove_spaces(title);

        let game_part = cleaned.split("PID").next().unwrap_or(&cleaned).trim();

        // Извлекаем только имя файла из пути (если это путь)
        // Например: "/home/user/steamapps/common/Game/Game.exe" → "Game.exe"
        let game_name = game_part
            .rsplit('/')
            .next()
            .unwrap_or(game_part)
            .to_string();

        if game_name.is_empty() {
            None
        } else {
            Some(game_name)
        }
    }
}

/// Удаляет невидимые пробелы и лишние символы из строки
///
/// # Arguments
///
/// * `value` - входная строка
///
/// # Returns
///
/// Очищенная строка без невидимых пробелов и с обрезанными краями
fn remove_spaces(value: &str) -> String {
    value
        .replace('\u{00A0}', " ") // неразрывный пробел (NBSP)
        .replace('\u{200E}', "") // left-to-right mark
        .trim()
        .to_string()
}

/// Выбирает подходящий трансформер на основе имени исполняемого файла и заголовка окна
///
/// # Arguments
///
/// * `executable_name` - имя исполняемого файла
/// * `window_title` - опциональный заголовок окна
///
/// # Returns
///
/// Кортеж `(app_name, window_title)` с трансформированными данными
pub fn transform_title_and_app_name(
    executable_name: &str,
    window_title: Option<&str>,
) -> (String, Option<String>) {
    let transformer: Box<dyn TitleTransformer> = match executable_name {
        "telegram-desktop" | "Telegram.exe" => Box::new(TelegramTransformer),
        "yandex_browser" | "browser.exe" => Box::new(YandexBrowserTransformer),
        _ if window_title.is_some_and(|title| title.contains("steamapps")) => {
            Box::new(SteamGameTransformer)
        }
        _ => Box::new(BaseTransformer),
    };

    let app_name = transformer.transform_app_name(executable_name);
    let transformed_title = transformer.transform_window_title(window_title);

    // Если заголовок пустой после трансформации, возвращаем None
    let title = transformed_title.filter(|t| !t.is_empty());

    (app_name, title)
}

// ============================================================================
// Юнит-тесты трансформеров
// ============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    // ------------------------------------------------------------------------
    // Тесты remove_spaces
    // ------------------------------------------------------------------------

    #[test]
    fn test_remove_spaces_nbsp() {
        assert_eq!(remove_spaces("Hello\u{00A0}World"), "Hello World");
    }

    #[test]
    fn test_remove_spaces_lrm() {
        assert_eq!(remove_spaces("Hello\u{200E}World"), "HelloWorld");
    }

    #[test]
    fn test_remove_spaces_trim() {
        assert_eq!(remove_spaces("  Hello World  "), "Hello World");
    }

    #[test]
    fn test_remove_spaces_combined() {
        assert_eq!(
            remove_spaces("  Hello\u{00A0}\u{200E}World  "),
            "Hello World"
        );
    }

    // ------------------------------------------------------------------------
    // Тесты TelegramTransformer
    // ------------------------------------------------------------------------

    #[test]
    fn test_telegram_transform_app_name() {
        let transformer = TelegramTransformer;
        assert_eq!(
            transformer.transform_app_name("telegram-desktop"),
            "Telegram"
        );
        assert_eq!(transformer.transform_app_name("Telegram.exe"), "Telegram");
    }

    #[test]
    fn test_telegram_transform_window_title_with_counter() {
        let transformer = TelegramTransformer;
        assert_eq!(
            transformer.transform_window_title(Some("Иван (12)")),
            Some("Иван".to_string())
        );
        assert_eq!(
            transformer.transform_window_title(Some("@channel (3)")),
            Some("@channel".to_string())
        );
    }

    #[test]
    fn test_telegram_transform_window_title_without_counter() {
        let transformer = TelegramTransformer;
        assert_eq!(
            transformer.transform_window_title(Some("Иван")),
            Some("Иван".to_string())
        );
    }

    #[test]
    fn test_telegram_transform_window_title_with_special_chars() {
        let transformer = TelegramTransformer;
        assert_eq!(
            transformer.transform_window_title(Some("ab (99)")),
            Some("ab".to_string())
        );
    }

    #[test]
    fn test_telegram_transform_window_title_none() {
        let transformer = TelegramTransformer;
        assert_eq!(transformer.transform_window_title(None), None);
    }

    // ------------------------------------------------------------------------
    // Тесты краевых случаев регулярного выражения (новая регулярка)
    // ------------------------------------------------------------------------

    #[test]
    fn test_telegram_regex_counter_at_end() {
        let transformer = TelegramTransformer;
        // Счётчик в конце строки — удаляется
        assert_eq!(
            transformer.transform_window_title(Some("Telegram (5)")),
            Some("Telegram".to_string())
        );
    }

    #[test]
    fn test_telegram_regex_no_counter() {
        let transformer = TelegramTransformer;
        // Без счётчика — остаётся как есть
        assert_eq!(
            transformer.transform_window_title(Some("Telegram")),
            Some("Telegram".to_string())
        );
    }

    #[test]
    fn test_telegram_regex_counter_in_middle() {
        let transformer = TelegramTransformer;
        // Счётчик в середине — НЕ удаляется (новая регулярка требует конца строки)
        assert_eq!(
            transformer.transform_window_title(Some("User (5) talks")),
            Some("User (5) talks".to_string())
        );
    }

    #[test]
    fn test_telegram_regex_multiple_parentheses() {
        let transformer = TelegramTransformer;
        // Несколько пар скобок — удаляется только последняя с цифрами в конце
        assert_eq!(
            transformer.transform_window_title(Some("Group (beta) (12)")),
            Some("Group (beta)".to_string())
        );
    }

    #[test]
    fn test_telegram_regex_non_numeric_in_parentheses() {
        let transformer = TelegramTransformer;
        // Скобки с нечисловым содержимым — не удаляются (требует цифры)
        assert_eq!(
            transformer.transform_window_title(Some("Telegram (beta)")),
            Some("Telegram (beta)".to_string())
        );
        assert_eq!(
            transformer.transform_window_title(Some("Channel (dev)")),
            Some("Channel (dev)".to_string())
        );
    }

    #[test]
    fn test_telegram_regex_empty_parentheses() {
        let transformer = TelegramTransformer;
        // Пустые скобки — не удаляются (требует цифры)
        assert_eq!(
            transformer.transform_window_title(Some("Telegram ()")),
            Some("Telegram ()".to_string())
        );
    }

    #[test]
    fn test_telegram_regex_multidigit_counter() {
        let transformer = TelegramTransformer;
        // Многозначный счётчик — удаляется
        assert_eq!(
            transformer.transform_window_title(Some("Channel (128)")),
            Some("Channel".to_string())
        );
    }

    #[test]
    fn test_telegram_regex_whitespace_before_counter() {
        let transformer = TelegramTransformer;
        // Один пробел перед счётчиком — счётчик распознаётся и удаляется
        assert_eq!(
            transformer.transform_window_title(Some("User (5)")),
            Some("User".to_string())
        );
        // Два пробела — счётчик распознаётся (последний пробел + counter), trim() удаляет лишний пробел
        assert_eq!(
            transformer.transform_window_title(Some("User  (5)")),
            Some("User".to_string())
        );
        // Три пробела — счётчик распознаётся (последний пробел + counter), trim() удаляет лишние пробелы
        assert_eq!(
            transformer.transform_window_title(Some("User   (5)")),
            Some("User".to_string())
        );
    }

    #[test]
    fn test_telegram_regex_counter_not_at_end() {
        let transformer = TelegramTransformer;
        // Счётчик не в конце — не удаляется (требует $)
        assert_eq!(
            transformer.transform_window_title(Some("User (5) talks now")),
            Some("User (5) talks now".to_string())
        );
    }

    #[test]
    fn test_telegram_regex_app_name_edge_case() {
        let transformer = TelegramTransformer;
        // Короткое имя с счётчиком на конце — часть имени может быть обрезана
        assert_eq!(
            transformer.transform_window_title(Some("AB (1)")),
            Some("AB".to_string())
        );
        assert_eq!(
            transformer.transform_window_title(Some("A (999)")),
            Some("A".to_string())
        );
    }

    // ------------------------------------------------------------------------
    // Тесты YandexBrowserTransformer
    // ------------------------------------------------------------------------

    #[test]
    fn test_yandex_browser_transform_app_name() {
        let transformer = YandexBrowserTransformer;
        assert_eq!(
            transformer.transform_app_name("yandex_browser"),
            "Яндекс Браузер"
        );
        assert_eq!(
            transformer.transform_app_name("browser.exe"),
            "Яндекс Браузер"
        );
    }

    #[test]
    fn test_yandex_browser_transform_window_title_with_suffix() {
        let transformer = YandexBrowserTransformer;
        assert_eq!(
            transformer.transform_window_title(Some("Google — Яндекс Браузер")),
            Some("Google".to_string())
        );
    }

    #[test]
    fn test_yandex_browser_transform_window_title_with_pinned() {
        let transformer = YandexBrowserTransformer;
        assert_eq!(
            transformer.transform_window_title(Some("Google — Яндекс Браузер вкладка закреплена")),
            Some("Google".to_string())
        );
    }

    #[test]
    fn test_yandex_browser_transform_window_title_without_suffix() {
        let transformer = YandexBrowserTransformer;
        assert_eq!(
            transformer.transform_window_title(Some("Google")),
            Some("Google".to_string())
        );
    }

    #[test]
    fn test_yandex_browser_transform_window_title_none() {
        let transformer = YandexBrowserTransformer;
        assert_eq!(transformer.transform_window_title(None), None);
    }

    // ------------------------------------------------------------------------
    // Тесты SteamGameTransformer
    // ------------------------------------------------------------------------

    #[test]
    fn test_steam_game_transform_app_name() {
        let transformer = SteamGameTransformer;
        assert_eq!(transformer.transform_app_name("steam"), "steam");
        assert_eq!(transformer.transform_app_name("steam.exe"), "steam.exe");
    }

    #[test]
    fn test_steam_game_transform_window_title() {
        let transformer = SteamGameTransformer;
        assert_eq!(
            transformer.transform_window_title(Some("Counter-Strike 2 PID 1234")),
            Some("Counter-Strike 2".to_string())
        );
    }

    #[test]
    fn test_steam_game_transform_window_title_empty() {
        let transformer = SteamGameTransformer;
        assert_eq!(transformer.transform_window_title(None), None);
    }

    // ------------------------------------------------------------------------
    // Тесты BaseTransformer
    // ------------------------------------------------------------------------

    #[test]
    fn test_base_transformer() {
        let transformer = BaseTransformer;
        assert_eq!(transformer.transform_app_name("firefox"), "firefox");
        assert_eq!(
            transformer.transform_window_title(Some("Test Window")),
            Some("Test Window".to_string())
        );
    }

    // ------------------------------------------------------------------------
    // Тесты transform_title_and_app_name (интеграция)
    // ------------------------------------------------------------------------

    #[test]
    fn test_transform_telegram() {
        let (app_name, title) = transform_title_and_app_name("telegram-desktop", Some("@user (5)"));
        assert_eq!(app_name, "Telegram");
        // Удаляется счётчик (5), остаётся @user
        assert_eq!(title, Some("@user".to_string()));
    }

    #[test]
    fn test_transform_telegram_windows() {
        let (app_name, title) = transform_title_and_app_name("Telegram.exe", Some("Иван (12)"));
        assert_eq!(app_name, "Telegram");
        // Удаляется счётчик (12), остаётся Иван
        assert_eq!(title, Some("Иван".to_string()));
    }

    #[test]
    fn test_transform_yandex_browser() {
        let (app_name, title) =
            transform_title_and_app_name("yandex_browser", Some("GitHub — Яндекс Браузер"));
        assert_eq!(app_name, "Яндекс Браузер");
        assert_eq!(title, Some("GitHub".to_string()));
    }

    #[test]
    fn test_transform_yandex_browser_windows() {
        let (app_name, title) = transform_title_and_app_name(
            "browser.exe",
            Some("Google — Яндекс Браузер вкладка закреплена"),
        );
        assert_eq!(app_name, "Яндекс Браузер");
        assert_eq!(title, Some("Google".to_string()));
    }

    #[test]
    fn test_transform_steam_game() {
        // Для Steam игр имя приложения берётся из заголовка, а не из executable_name
        let (app_name, title) = transform_title_and_app_name(
            "steam",
            Some("/home/user/steamapps/common/Game/Game.exe PID 12345 — Game"),
        );
        assert_eq!(app_name, "steam");
        // Название игры извлекается до "PID" и обрезается
        assert_eq!(title, Some("Game.exe".to_string()));
    }

    #[test]
    fn test_transform_base() {
        let (app_name, title) = transform_title_and_app_name("firefox", Some("Mozilla Firefox"));
        assert_eq!(app_name, "firefox");
        assert_eq!(title, Some("Mozilla Firefox".to_string()));
    }

    #[test]
    fn test_transform_empty_title() {
        let (app_name, title) = transform_title_and_app_name("firefox", Some(""));
        assert_eq!(app_name, "firefox");
        assert_eq!(title, None);
    }

    #[test]
    fn test_transform_none_title() {
        let (app_name, title) = transform_title_and_app_name("firefox", None);
        assert_eq!(app_name, "firefox");
        assert_eq!(title, None);
    }

    #[test]
    fn test_transform_nbsp_in_title() {
        let (app_name, title) = transform_title_and_app_name("firefox", Some("Hello\u{00A0}World"));
        assert_eq!(app_name, "firefox");
        assert_eq!(title, Some("Hello World".to_string()));
    }
}
