-- Bật foreign key constraints
PRAGMA foreign_keys = ON;

-- Tạo bảng chat_history với phân quyền theo user
CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    session_id TEXT,
    is_private BOOLEAN DEFAULT 1,
    status TEXT DEFAULT 'active',
    message_type TEXT DEFAULT 'text',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Tạo index để tối ưu truy vấn
CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_timestamp ON chat_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_chat_history_session ON chat_history(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_status ON chat_history(status);
CREATE INDEX IF NOT EXISTS idx_chat_history_user_session ON chat_history(user_id, session_id);

-- Tạo bảng chat_sessions để quản lý session chat
CREATE TABLE IF NOT EXISTS chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    title TEXT DEFAULT 'New Chat',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Index cho chat_sessions
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_session_id ON chat_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_active ON chat_sessions(is_active);

-- Tạo trigger để tự động cập nhật updated_at
CREATE TRIGGER IF NOT EXISTS update_chat_history_timestamp
    AFTER UPDATE ON chat_history
BEGIN
    UPDATE chat_history SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_chat_sessions_timestamp
    AFTER UPDATE ON chat_sessions
BEGIN
    UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger để cập nhật last_activity khi có tin nhắn mới
CREATE TRIGGER IF NOT EXISTS update_session_activity
    AFTER INSERT ON chat_history
BEGIN
    UPDATE chat_sessions 
    SET last_activity = CURRENT_TIMESTAMP
    WHERE session_id = NEW.session_id;
END;

-- View để lấy thống kê chat theo user
CREATE VIEW IF NOT EXISTS user_chat_stats AS
SELECT 
    u.id as user_id,
    u.username,
    u.role,
    COUNT(DISTINCT cs.session_id) as total_sessions,
    COUNT(ch.id) as total_messages,
    MAX(ch.timestamp) as last_chat_time,
    MIN(ch.timestamp) as first_chat_time
FROM users u
LEFT JOIN chat_sessions cs ON u.id = cs.user_id
LEFT JOIN chat_history ch ON u.id = ch.user_id
GROUP BY u.id, u.username, u.role;

-- View để lấy chat history với thông tin user
CREATE VIEW IF NOT EXISTS chat_history_with_user AS
SELECT 
    ch.id,
    ch.user_id,
    u.username,
    u.role,
    ch.message,
    ch.response,
    ch.timestamp,
    ch.session_id,
    ch.is_private,
    ch.status,
    ch.message_type,
    cs.title as session_title
FROM chat_history ch
JOIN users u ON ch.user_id = u.id
LEFT JOIN chat_sessions cs ON ch.session_id = cs.session_id
WHERE ch.status = 'active'
ORDER BY ch.timestamp DESC;