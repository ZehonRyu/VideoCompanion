import sqlite3

def look_database(db_path='video_site.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    tables_to_display = ["videos", "folders", "folder_video_rel", "likes", "tags", "video_tags"]

    for table in tables_to_display:
        print(f"\n=== {table.upper()} ===")
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [column[1] for column in cursor.fetchall()]
        print(" | ".join(columns))

        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        for row in rows:
            print(" | ".join(str(item) for item in row))

    conn.close()
    print("\nDatabase display complete.")

if __name__ == '__main__':
    look_database()