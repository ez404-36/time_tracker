//! Дизайн-система и CSS-переменные

use crate::state::Theme;
use dioxus::prelude::*;

/// Провайдер темы
#[derive(Clone)]
pub struct ThemeProvider {
    theme: Signal<Theme>,
}

impl ThemeProvider {
    pub fn new(initial_theme: Theme) -> Self {
        Self {
            theme: Signal::new(initial_theme),
        }
    }

    pub fn toggle(&mut self) {
        let current = *self.theme.read();
        self.theme.set(current.toggle());
    }

    pub fn get_css(&self) -> String {
        let theme = *self.theme.read();

        let (theme_name, css_theme) = match theme {
            Theme::Light => ("light", LIGHT_THEME_CSS),
            Theme::Dark => ("dark", DARK_THEME_CSS),
        };

        format!(
            r#"
:root {{
    /* Размеры шрифтов (из ui/consts.py: FontSize) */
    --font-size-small: 12px;
    --font-size-regular: 14px;
    --font-size-h5: 16px;
    --font-size-h4: 18px;
    --font-size-h3: 24px;
    --font-size-h2: 36px;
    --font-size-h1: 48px;

    /* Начертания шрифтов */
    --font-weight-normal: 400;
    --font-weight-bold: 700;
}}

[data-theme="{theme_name}" ] {{
    {css_theme}
}}

/* Базовые стили */
* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: system-ui, -apple-system, "Segoe UI", "Roboto", "Helvetica", "Arial", sans-serif;
    font-size: var(--font-size-regular);
    color: var(--text-primary);
    background-color: var(--bg-primary);
    line-height: 1.5;
}}

/* Контейнер приложения */
.app-container {{
    display: flex;
    height: 100vh;
    overflow: hidden;
}}

/* Боковая панель */
.sidebar {{
    width: 200px;
    background-color: var(--nav-bg);
    display: flex;
    flex-direction: column;
    border-right: 1px solid var(--border-color);
}}

.sidebar-header {{
    padding: 24px 16px;
    font-size: var(--font-size-h3);
    font-weight: var(--font-weight-bold);
    color: var(--nav-text);
    border-bottom: 1px solid var(--border-color);
}}

.sidebar-nav {{
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 8px;
}}

/* Элементы навигации */
.nav-item {{
    padding: 12px 16px;
    border: none;
    background: none;
    text-align: left;
    font-size: var(--font-size-regular);
    font-weight: var(--font-weight-normal);
    color: var(--nav-text);
    cursor: pointer;
    border-radius: 6px;
    transition: background-color 0.2s;
}}

.nav-item:hover {{
    background-color: var(--bg-tertiary);
}}

.nav-item.active {{
    background-color: var(--nav-active);
    color: var(--nav-active-text);
    font-weight: var(--font-weight-bold);
}}

/* Основной контент */
.main-content {{
    flex: 1;
    padding: 24px;
    overflow-y: auto;
    background-color: var(--bg-primary);
}}

/* Заглушка раздела */
.section-placeholder {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    gap: 16px;
}}

.section-title {{
    font-size: var(--font-size-h2);
    font-weight: var(--font-weight-bold);
    color: var(--text-primary);
}}

.section-hint {{
    font-size: var(--font-size-regular);
    color: var(--text-secondary);
}}

/* Snackbar для уведомлений */
.snackbar {{
    position: fixed;
    bottom: 24px;
    right: 24px;
    background-color: var(--color-black);
    color: var(--color-white);
    padding: 16px 24px;
    border-radius: 4px;
    box-shadow: var(--shadow-lg);
    font-size: var(--font-size-regular);
    animation: slideIn 0.3s ease-out;
}}

@keyframes slideIn {{
    from {{
        transform: translateY(100%);
        opacity: 0;
    }}
    to {{
        transform: translateY(0);
        opacity: 1;
    }}
}}
"#
        )
    }
}

/// Хук для получения текущей темы
pub fn use_theme(provider: &ThemeProvider) -> ThemeProvider {
    provider.clone()
}

const LIGHT_THEME_CSS: &str = r#"
    /* Фон */
    --bg-primary: #ffffff;
    --bg-secondary: #f5f5f5;
    --bg-tertiary: #e0e0e0;

    /* Текст */
    --text-primary: #1a1a1a;
    --text-secondary: #666666;
    --text-tertiary: #999999;
    --text-inverse: #ffffff;

    /* Основные цвета (Primary/Secondary) */
    --color-primary: #2c64c8;
    --color-secondary: #ff9500;

    /* Статусные цвета */
    --color-red-light: #ef9a9a;
    --color-red: #f44336;
    --color-blue-light: #90caf9;
    --color-blue: #2196f3;
    --color-green-light: #a5d6a7;
    --color-green: #4caf50;
    --color-grey: #9e9e9e;
    --color-grey-light: #e0e0e0;
    --color-black: #000000;
    --color-white: #ffffff;

    /* Границы и разделители */
    --border-color: #e0e0e0;
    --border-focus: #2c64c8;

    /* Тени */
    --shadow-sm: 0 1px 2px rgba(0,0,0,0.1);
    --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
    --shadow-lg: 0 10px 25px rgba(0,0,0,0.15);

    /* Навигация */
    --nav-bg: #f5f5f5;
    --nav-text: #1a1a1a;
    --nav-active: #2c64c8;
    --nav-active-text: #ffffff;
"#;

const DARK_THEME_CSS: &str = r#"
    /* Фон */
    --bg-primary: #1e1e1e;
    --bg-secondary: #2d2d2d;
    --bg-tertiary: #3d3d3d;

    /* Текст */
    --text-primary: #ffffff;
    --text-secondary: #b0b0b0;
    --text-tertiary: #808080;
    --text-inverse: #000000;

    /* Основные цвета */
    --color-primary: #64b5f6;
    --color-secondary: #ffb74d;

    /* Статусные цвета (адаптированы для тёмной темы) */
    --color-red-light: #ef5350;
    --color-red: #f44336;
    --color-blue-light: #42a5f5;
    --color-blue: #2196f3;
    --color-green-light: #66bb6a;
    --color-green: #4caf50;
    --color-grey: #6e6e6e;
    --color-grey-light: #424242;
    --color-black: #000000;
    --color-white: #ffffff;

    /* Границы и разделители */
    --border-color: #404040;
    --border-focus: #64b5f6;

    /* Тени */
    --shadow-sm: 0 1px 2px rgba(0,0,0,0.3);
    --shadow-md: 0 4px 6px rgba(0,0,0,0.3);
    --shadow-lg: 0 10px 25px rgba(0,0,0,0.4);

    /* Навигация */
    --nav-bg: #2d2d2d;
    --nav-text: #ffffff;
    --nav-active: #64b5f6;
    --nav-active-text: #000000;
"#;
