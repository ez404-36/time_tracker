-- Базовая миграция: 5 таблиц TimeTracker
-- Таблица event из Python-версии не создаётся — заменена на файловые логи

-- Таблица task: задачи с дедлайнами и вложенностью
CREATE TABLE task (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(50) NOT NULL,
    description TEXT,
    created_at DATETIME NOT NULL,
    parent_id INTEGER,
    deadline_date DATE,
    deadline_time TIME,
    is_done BOOLEAN NOT NULL DEFAULT 0,
    is_expired BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (parent_id) REFERENCES task(id) ON DELETE SET NULL
);
CREATE INDEX task_parent_id ON task(parent_id);

-- Таблица window_session: сессии активности в приложениях
CREATE TABLE window_session (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_ts DATETIME NOT NULL,
    end_ts DATETIME,
    duration INTEGER NOT NULL,
    executable_name VARCHAR(255) NOT NULL,
    executable_path VARCHAR(255),
    window_title VARCHAR(255)
);

-- Таблица idle_session: сессии бездействия
CREATE TABLE idle_session (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_ts DATETIME NOT NULL,
    end_ts DATETIME,
    duration INTEGER NOT NULL
);

-- Таблица settings: настройки приложения (singleton)
CREATE TABLE settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_timezone VARCHAR(255) NOT NULL DEFAULT 'Europe/Moscow',
    idle_threshold INTEGER NOT NULL DEFAULT 60,
    enable_window_tracking BOOLEAN NOT NULL DEFAULT 0,
    enable_idle_tracking BOOLEAN NOT NULL DEFAULT 0,
    enable_pomodoro BOOLEAN NOT NULL DEFAULT 0,
    pomodoro_work_time SMALLINT,
    pomodoro_rest_time SMALLINT,
    ui_settings JSON NOT NULL DEFAULT '{}',
    task_deadline_sound_config_id INTEGER,
    idle_sound_config_id INTEGER,
    pomodoro_sound_config_id INTEGER,
    autostart_enabled BOOLEAN NOT NULL DEFAULT 0,
    start_minimized BOOLEAN NOT NULL DEFAULT 0,
    close_to_tray BOOLEAN NOT NULL DEFAULT 0,
    autostart_tracking BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (task_deadline_sound_config_id) REFERENCES settings_audio_param(id) ON DELETE SET NULL,
    FOREIGN KEY (idle_sound_config_id) REFERENCES settings_audio_param(id) ON DELETE SET NULL,
    FOREIGN KEY (pomodoro_sound_config_id) REFERENCES settings_audio_param(id) ON DELETE SET NULL
);
CREATE INDEX settings_task_deadline_sound_config_id ON settings(task_deadline_sound_config_id);
CREATE INDEX settings_idle_sound_config_id ON settings(idle_sound_config_id);
CREATE INDEX settings_pomodoro_sound_config_id ON settings(pomodoro_sound_config_id);

-- Таблица settings_audio_param: параметры звуковых уведомлений
CREATE TABLE settings_audio_param (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    disabled BOOLEAN NOT NULL DEFAULT 0,
    sound VARCHAR(255),
    volume_offset DECIMAL(3,1) NOT NULL DEFAULT 0.0
);
