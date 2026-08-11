//! Дизайн-система и CSS-переменные

use crate::state::Theme;

/// Возвращает CSS с учётом темы
pub fn get_theme_css(_theme: Theme) -> String {
    let (light_css, dark_css) = get_theme_css_strings();

    format!(
        r#"
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

:root {{
    --font-size-small: 12px;
    --font-size-regular: 14px;
    --font-size-h5: 16px;
    --font-size-h4: 18px;
    --font-size-h3: 24px;
    --font-size-h2: 36px;
    --font-size-h1: 48px;
    --font-weight-normal: 400;
    --font-weight-bold: 700;
}}

[data-theme="light"] {{
    {light_css}
}}

[data-theme="dark"] {{
    {dark_css}
}}

.app-container {{
    display: flex;
    flex-direction: column;
    height: 100vh;
    overflow: hidden;
}}

.app-layout {{
    display: flex;
    flex: 1;
    overflow: hidden;
}}

.sidebar {{
    width: 0;
    overflow: hidden;
    background-color: var(--nav-bg);
    border-right: 1px solid var(--border-color);
    transition: width 0.3s ease;
}}

.sidebar.visible {{
    width: 240px;
}}

.sidebar-nav {{
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 16px;
}}

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

.main-content {{
    flex: 1;
    padding: 24px;
    overflow-y: auto;
    background-color: var(--bg-primary);
}}

.section-placeholder {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    gap: 16px;
}}

.section-icon {{
    font-size: 64px;
    margin-bottom: 16px;
}}

.section-title {{
    font-size: var(--font-size-h2);
    font-weight: var(--font-weight-bold);
    color: var(--text-primary);
}}

.section-description {{
    font-size: var(--font-size-regular);
    color: var(--text-secondary);
    margin-bottom: 8px;
}}

.section-hint {{
    font-size: var(--font-size-regular);
    color: var(--text-tertiary);
}}

.app-bar {{
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 12px 24px;
    background-color: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
    height: 56px;
}}

.app-bar-menu-button {{
    background: none;
    border: none;
    font-size: 24px;
    cursor: pointer;
    padding: 8px;
    border-radius: 4px;
    transition: background-color 0.2s;
}}

.app-bar-menu-button:hover {{
    background-color: var(--bg-tertiary);
}}

.app-bar-title {{
    font-size: var(--font-size-h4);
    font-weight: var(--font-weight-bold);
    color: var(--text-primary);
}}

.app-bar-spacer {{
    flex: 1;
}}

.app-bar-version {{
    font-size: var(--font-size-small);
    color: var(--text-secondary);
}}

.app-bar-theme-button {{
    background: none;
    border: none;
    font-size: 20px;
    cursor: pointer;
    padding: 8px;
    border-radius: 4px;
    transition: background-color 0.2s;
}}

.app-bar-theme-button:hover {{
    background-color: var(--bg-tertiary);
}}

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
    display: flex;
    align-items: center;
    gap: 12px;
    animation: slideIn 0.3s ease-out;
    z-index: 1000;
}}

.snackbar-close {{
    background: none;
    border: none;
    color: var(--color-white);
    font-size: 18px;
    cursor: pointer;
    padding: 0;
    margin-left: 8px;
    opacity: 0.8;
    transition: opacity 0.2s;
}}

.snackbar-close:hover {{
    opacity: 1;
}}

.modal-overlay {{
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2000;
    animation: fadeIn 0.2s ease-out;
}}

.modal {{
    background-color: var(--bg-primary);
    border-radius: 8px;
    box-shadow: var(--shadow-lg);
    min-width: 400px;
    max-width: 600px;
    animation: modalSlideIn 0.3s ease-out;
}}

.modal-header {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 24px;
    border-bottom: 1px solid var(--border-color);
}}

.modal-icon {{
    font-size: 32px;
}}

.modal-title {{
    font-size: var(--font-size-h4);
    font-weight: var(--font-weight-bold);
    color: var(--text-primary);
    margin: 0;
}}

.modal-body {{
    padding: 24px;
}}

.modal-body p {{
    font-size: var(--font-size-regular);
    color: var(--text-primary);
    line-height: 1.6;
}}

.modal-footer {{
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    padding: 16px 24px;
    border-top: 1px solid var(--border-color);
}}

.modal-button {{
    padding: 10px 24px;
    border: none;
    border-radius: 4px;
    font-size: var(--font-size-regular);
    font-weight: var(--font-weight-normal);
    cursor: pointer;
    transition: background-color 0.2s;
}}

.modal-button-cancel {{
    background-color: var(--bg-secondary);
    color: var(--text-primary);
}}

.modal-button-cancel:hover {{
    background-color: var(--bg-tertiary);
}}

.modal-button-confirm {{
    background-color: var(--color-primary);
    color: var(--color-white);
}}

.modal-button-confirm:hover {{
    opacity: 0.9;
}}

.loading-screen {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100vh;
    background-color: var(--bg-primary);
}}

.loading-spinner {{
    width: 40px;
    height: 40px;
    border: 4px solid var(--bg-tertiary);
    border-top: 4px solid var(--color-primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}}

@keyframes spin {{
    0% {{ transform: rotate(0deg); }}
    100% {{ transform: rotate(360deg); }}
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

@keyframes fadeIn {{
    from {{
        opacity: 0;
    }}
    to {{
        opacity: 1;
    }}
}}

@keyframes modalSlideIn {{
    from {{
        transform: scale(0.9);
        opacity: 0;
    }}
    to {{
        transform: scale(1);
        opacity: 1;
    }}
}}
"#
    )
}

fn get_theme_css_strings() -> (&'static str, &'static str) {
    let light_css = r#"
    --bg-primary: #ffffff;
    --bg-secondary: #f5f5f5;
    --bg-tertiary: #e0e0e0;
    --text-primary: #1a1a1a;
    --text-secondary: #666666;
    --text-tertiary: #999999;
    --text-inverse: #ffffff;
    --color-primary: #2c64c8;
    --color-secondary: #ff9500;
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
    --border-color: #e0e0e0;
    --border-focus: #2c64c8;
    --shadow-sm: 0 1px 2px rgba(0,0,0,0.1);
    --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
    --shadow-lg: 0 10px 25px rgba(0,0,0,0.15);
    --nav-bg: #f5f5f5;
    --nav-text: #1a1a1a;
    --nav-active: #2c64c8;
    --nav-active-text: #ffffff;
"#;

    let dark_css = r#"
    --bg-primary: #1e1e1e;
    --bg-secondary: #2d2d2d;
    --bg-tertiary: #3d3d3d;
    --text-primary: #ffffff;
    --text-secondary: #b0b0b0;
    --text-tertiary: #808080;
    --text-inverse: #000000;
    --color-primary: #64b5f6;
    --color-secondary: #ffb74d;
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
    --border-color: #404040;
    --border-focus: #64b5f6;
    --shadow-sm: 0 1px 2px rgba(0,0,0,0.3);
    --shadow-md: 0 4px 6px rgba(0,0,0,0.3);
    --shadow-lg: 0 10px 25px rgba(0,0,0,0.4);
    --nav-bg: #2d2d2d;
    --nav-text: #ffffff;
    --nav-active: #64b5f6;
    --nav-active-text: #000000;
"#;

    (light_css, dark_css)
}
