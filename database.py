import sqlite3
from datetime import datetime

DATABASE_NAME = "scheduler.db"

def connect_db():
    """Kết nối tới CSDL và trả về đối tượng connection."""
    return sqlite3.connect(DATABASE_NAME)

def init_db():
    """Khởi tạo bảng events nếu chưa tồn tại."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            location TEXT,
            reminder_minutes INTEGER
        )
    """)
    conn.commit()
    conn.close()

def add_event(name, start_time, end_time, location, reminder_minutes):
    """Thêm một sự kiện mới vào CSDL."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO events (name, start_time, end_time, location, reminder_minutes) VALUES (?, ?, ?, ?, ?)",
        (name, start_time, end_time, location, reminder_minutes)
    )
    conn.commit()
    conn.close()

def update_event(event_id, name, start_time, end_time, location, reminder_minutes):
    """Cập nhật thông tin sự kiện dựa trên ID."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE events 
        SET name = ?, start_time = ?, end_time = ?, location = ?, reminder_minutes = ?
        WHERE id = ?
        """,
        (name, start_time, end_time, location, reminder_minutes, event_id)
    )
    conn.commit()
    conn.close()

def get_all_events():
    """Lấy tất cả các sự kiện, sắp xếp theo thời gian bắt đầu."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, start_time, end_time, location, reminder_minutes FROM events ORDER BY start_time ASC")
    events = cursor.fetchall()
    conn.close()
    return events

def delete_event(event_id):
    """Xóa sự kiện dựa trên ID."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()

def search_events_by_name(name_text):
    """Tìm kiếm sự kiện theo tên (không phân biệt chữ hoa/thường)."""
    conn = connect_db()
    cursor = conn.cursor()
    search_pattern = f"%{name_text}%"
    cursor.execute(
        "SELECT id, name, start_time, end_time, location, reminder_minutes FROM events WHERE name LIKE ? ORDER BY start_time ASC", 
        (search_pattern,)
    )
    events = cursor.fetchall()
    conn.close()
    return events

init_db()
