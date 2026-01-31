import sqlite3
import os

def migrate_guest_chat_tables():
    """Migration script để tạo guest chat tables trong accounts.db"""
    
    
    db_path = "accounts/Database/account.db"
    
    if not os.path.exists(db_path):
        print(f"Database không tồn tại: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        cur = conn.cursor()
        
        print("🔄 Bắt đầu migration guest chat tables...")
        
       
        cur.execute("""
            CREATE TABLE IF NOT EXISTS guest_sessions (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                session_name TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                message_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        print("✅ Tạo bảng guest_sessions thành công")
        
       
        cur.execute("""
            CREATE TABLE IF NOT EXISTS guest_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                response TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                source TEXT DEFAULT 'hybrid',
                decision_info TEXT,
                FOREIGN KEY (session_id) REFERENCES guest_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        print("✅ Tạo bảng guest_messages thành công")
        
        # Tạo indexes
        indexes = [
            ("idx_guest_sessions_user_id", "CREATE INDEX IF NOT EXISTS idx_guest_sessions_user_id ON guest_sessions(user_id)"),
            ("idx_guest_messages_session_id", "CREATE INDEX IF NOT EXISTS idx_guest_messages_session_id ON guest_messages(session_id)"),
            ("idx_guest_messages_user_id", "CREATE INDEX IF NOT EXISTS idx_guest_messages_user_id ON guest_messages(user_id)"),
            ("idx_guest_messages_timestamp", "CREATE INDEX IF NOT EXISTS idx_guest_messages_timestamp ON guest_messages(timestamp)")
        ]
        
        for index_name, index_sql in indexes:
            cur.execute(index_sql)
            print(f"✅ Tạo index {index_name} thành công")
        
        conn.commit()
        print("🎉 Migration hoàn thành!")
        
        # Kiểm tra kết quả
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'guest_%'")
        tables = cur.fetchall()
        print(f"📊 Tables created: {[table[0] for table in tables]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi migration: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_guest_chat_tables()