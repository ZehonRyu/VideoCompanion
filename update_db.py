import os
import sqlite3
import time
from moviepy.editor import VideoFileClip

# 数据库连接和创建
def create_database(db_path='video_site.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    create_tables_script = """
    -- 视频表
    CREATE TABLE IF NOT EXISTS videos (
        video_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        file_path TEXT UNIQUE,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        duration INTEGER,
        like_count INTEGER DEFAULT 0
    );

    -- 文件夹表
    CREATE TABLE IF NOT EXISTS folders (
        folder_id INTEGER PRIMARY KEY AUTOINCREMENT,
        parent_folder_id INTEGER REFERENCES folders(folder_id) ON DELETE CASCADE,
        folder_name TEXT,
        creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- 文件夹-视频关联表
    CREATE TABLE IF NOT EXISTS folder_video_rel (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        folder_id INTEGER REFERENCES folders(folder_id) ON DELETE CASCADE,
        video_id INTEGER REFERENCES videos(video_id) ON DELETE CASCADE
    );

    -- 点赞记录表
    CREATE TABLE IF NOT EXISTS likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_id INTEGER REFERENCES videos(video_id) ON DELETE CASCADE,
        ip_address TEXT,
        like_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- 标签表
    CREATE TABLE IF NOT EXISTS tags (
        tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
        tag_name TEXT UNIQUE
    );

    -- 视频-标签关联表
    CREATE TABLE IF NOT EXISTS video_tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_id INTEGER REFERENCES videos(video_id) ON DELETE CASCADE,
        tag_id INTEGER REFERENCES tags(tag_id) ON DELETE CASCADE
    );

    -- 创建索引

    CREATE INDEX IF NOT EXISTS idx_folders_parent ON folders(parent_folder_id);
    CREATE INDEX IF NOT EXISTS idx_folder_video_folder ON folder_video_rel(folder_id);
    CREATE INDEX IF NOT EXISTS idx_folder_video_video ON folder_video_rel(video_id);
    CREATE INDEX IF NOT EXISTS idx_likes_ip_date ON likes(ip_address, like_date);
    CREATE INDEX IF NOT EXISTS idx_video_tags_video ON video_tags(video_id);
    CREATE INDEX IF NOT EXISTS idx_video_tags_tag ON video_tags(tag_id);
    """

    cursor.executescript(create_tables_script)
    conn.commit()
    print("Database and tables created.")
    return conn

# 获取或创建文件夹
def get_or_create_folder(cursor, folder_path):
    parent_path, folder_name = os.path.split(folder_path)
    cursor.execute("SELECT folder_id FROM folders WHERE folder_name = ?", (folder_path,))
    result = cursor.fetchone()
    if result:
        return result[0]

    if parent_path:
        parent_id = get_or_create_folder(cursor, parent_path)
    else:
        parent_id = None

    cursor.execute("INSERT INTO folders (parent_folder_id, folder_name) VALUES (?, ?)", (parent_id, folder_path))
    folder_id = cursor.lastrowid
    print(f"Folder created: {folder_path} (ID: {folder_id})")
    return folder_id

# 获取或创建视频
def get_or_create_video(cursor, title, file_path):
    cursor.execute("SELECT video_id FROM videos WHERE file_path = ?", (file_path,))
    result = cursor.fetchone()
    if result:
        return result[0]

    duration = get_video_duration(file_path)
    cursor.execute("INSERT INTO videos (title, file_path, duration) VALUES (?, ?, ?)", (title, file_path, duration))
    video_id = cursor.lastrowid
    print(f"Video created: {title} (ID: {video_id}, Duration: {duration} sec)")
    return video_id

# 关联视频与文件夹
def associate_video_with_folder(cursor, folder_id, video_id):
    cursor.execute("SELECT 1 FROM folder_video_rel WHERE folder_id = ? AND video_id = ?", (folder_id, video_id))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO folder_video_rel (folder_id, video_id) VALUES (?, ?)", (folder_id, video_id))
        print(f"Video (ID: {video_id}) associated with Folder (ID: {folder_id})")

# 获取视频时长
def get_video_duration(file_path):
    try:
        with VideoFileClip(file_path) as video:
            return int(video.duration)
    except Exception as e:
        print(f"Error getting duration for {file_path}: {e}")
        return 0

# 删除数据库中缺少的文件夹及其关联记录
def delete_missing_folders_and_videos(conn, base_folder='videos'):
    cursor = conn.cursor()
    cursor.execute("SELECT folder_id, folder_name FROM folders")
    all_folders = cursor.fetchall()

    for folder_id, folder_path in all_folders:
        if not os.path.exists(folder_path):
            cursor.execute("DELETE FROM folders WHERE folder_id = ?", (folder_id,))
            print(f"Folder and associated records deleted: {folder_path} (ID: {folder_id})")

    cursor.execute("SELECT video_id, file_path FROM videos")
    all_videos = cursor.fetchall()

    for video_id, file_path in all_videos:
        if not os.path.exists(file_path):
            cursor.execute("DELETE FROM videos WHERE video_id = ?", (video_id,))
            print(f"Video and associated records deleted: {file_path} (ID: {video_id})")

    conn.commit()

# 扫描文件夹，更新数据库
def scan_and_update_database(conn, base_folder='videos'):
    cursor = conn.cursor()

    for root, dirs, files in os.walk(base_folder):
        folder_id = get_or_create_folder(cursor, root)

        for file in files:
            if file.endswith(('.mp4', '.avi', '.mkv', '.mov')):
                file_path = os.path.join(root, file)
                video_id = get_or_create_video(cursor, file, file_path)
                associate_video_with_folder(cursor, folder_id, video_id)

    conn.commit()

if __name__ == '__main__':
    conn = create_database()
    delete_missing_folders_and_videos(conn)
    scan_and_update_database(conn)
    conn.close()
    print("Database scan and update complete.")