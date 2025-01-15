import datetime
import os
import re
from flask import Flask, render_template, request, redirect, send_from_directory, url_for, jsonify
import sqlite3
from datetime import datetime
import inspect

app = Flask(__name__)
DATABASE = 'video_site.db'

app.config['VIDEO_FOLDER'] = os.path.join(os.getcwd(), 'videos')  # 视频文件所在目录
print(f"VIDEO_FOLDER set to: {app.config['VIDEO_FOLDER']}")

def create_connection(db_file):
    """ 创建一个数据库连接到给定的SQLite数据库 """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
    except sqlite3.Error as e:
        print(e)
    return conn

def get_folder_info(conn, folder_id):
    """ 获取文件夹的信息及其子文件夹和视频 """
    cur_folders = conn.cursor()
    cur_folders.execute("SELECT folder_name, parent_folder_id FROM folders WHERE folder_id=?", (folder_id,))
    folder_data = cur_folders.fetchone()  # 返回单个元组
    if folder_data:
        folder_name = folder_data['folder_name']
        parent_folder_id = folder_data['parent_folder_id']
    else:
        return None  # 如果文件夹不存在，返回None

    # 获取子文件夹
    cur_folders.execute("SELECT folder_id, folder_name FROM folders WHERE parent_folder_id=?", (folder_id,))
    sub_folders = [{'id': row[0], 'name': row[1]} for row in cur_folders.fetchall()]

    # 获取视频
    cur_videos = conn.cursor()
    if folder_id == 1:
        # 如果 folder_id 为 1，返回所有视频
        cur_videos.execute(
            "SELECT video_id, title, like_count, duration, upload_date FROM videos"
        )
    else:
        # 否则，返回指定文件夹内的视频
        cur_videos.execute(
            "SELECT v.video_id, v.title, v.like_count, v.duration, v.upload_date "
            "FROM videos v JOIN folder_video_rel fvr ON v.video_id = fvr.video_id "
            "WHERE fvr.folder_id=?", (folder_id,)
        )
    videos = [{'video_id': row[0], 'title': row[1], 'like_count': row[2], 'duration': row[3], 'upload_date': row[4]} for row in cur_videos.fetchall()]

    return {
        'name': folder_name,
        'subFolders': sub_folders,
        'videos': videos,
        'currentFolderId': folder_id,
        'parentId': parent_folder_id
    }

@app.route('/')
def home():
    """ 主页，显示根文件夹的信息 """
    conn = create_connection(DATABASE)
    folder_info = get_folder_info(conn, 1)  # 假设根文件夹的ID为1
    conn.close()
    return render_template('index.html', folder_info=folder_info) #template_name模板文件名  context模板参数

@app.route('/folder/<int:folder_id>')
def folder(folder_id):
    """ 显示指定文件夹的信息 """
    print(f"Received request for folder_id: {folder_id}")
    conn = create_connection(DATABASE)
    folder_info = get_folder_info(conn, folder_id)
    conn.close()
    return render_template('index.html', folder_info=folder_info)

@app.route('/api/current_folder', methods=['GET'])
def api_current_folder():
    """ 返回当前文件夹的信息 """
    folder_id = request.args.get('folder_id', 1, type=int)
    conn = create_connection(DATABASE)
    folder_info = get_folder_info(conn, folder_id)
    conn.close()
    return jsonify(folder_info)

@app.route('/api/sorted_videos', methods=['GET'])
def api_sorted_videos():
    """ 返回排序后的视频列表 """
    sort_type = request.args.get('sort', '')
    folder_id_str = request.args.get('folder_id', '1')
    
    # 确保 folder_id 是一个有效的整数
    try:
        folder_id = int(folder_id_str)
    except ValueError:
        folder_id = 1  # 默认值为 1
        print(f"Invalid folder_id: {folder_id_str}, using default value: 1")

    print(f"folder_id: {folder_id}")

    conn = create_connection(DATABASE)
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    
    # 获取视频
    cur_videos = conn.cursor()
    if folder_id == 1:
        # 如果 folder_id 为 1，返回所有视频
        query = "SELECT video_id, title, like_count, duration, upload_date FROM videos"
        params = ()
    else:
        # 否则，返回指定文件夹内的视频
        query = "SELECT v.video_id, v.title, v.like_count, v.duration, v.upload_date FROM videos v JOIN folder_video_rel fvr ON v.video_id = fvr.video_id WHERE fvr.folder_id=?"
        params = (folder_id,)
    
    if sort_type == 'likeCountDesc':
        query += " ORDER BY like_count DESC"
    elif sort_type == 'likeCountAsc':
        query += " ORDER BY like_count ASC"
    elif sort_type == 'durationDesc':
        query += " ORDER BY duration DESC"
    elif sort_type == 'durationAsc':
        query += " ORDER BY duration ASC"
    elif sort_type == 'uploadDateDesc':
        query += " ORDER BY upload_date DESC"
    elif sort_type == 'uploadDateAsc':
        query += " ORDER BY upload_date ASC"
    
    print(f"Executing query: {query} with params: {params}")

    try:
        cur_videos.execute(query, params)
        videos = [{'video_id': row[0], 'title': row[1], 'like_count': row[2], 'duration': row[3], 'upload_date': row[4]} for row in cur_videos.fetchall()]
    except sqlite3.OperationalError as e:
        return jsonify({'error': str(e)}), 500
    
    # 获取子文件夹
    cur_folders = conn.cursor()
    cur_folders.execute("SELECT folder_id, folder_name FROM folders WHERE parent_folder_id=?", (folder_id,))
    sub_folders = [{'id': row[0], 'name': row[1]} for row in cur_folders.fetchall()]
    
    folder_info = {'name': '', 'subFolders': sub_folders, 'videos': videos}
    conn.close()
    return jsonify(folder_info)

@app.route('/api/video/<int:video_id>', methods=['GET'])
def get_video(video_id):
    conn = create_connection(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM videos WHERE video_id = ?
    """, (video_id,))
    video = cursor.fetchone()

    cursor.execute("""
        SELECT folder_id FROM folder_video_rel WHERE video_id = ?
    """, (video_id,))
    folder_id = cursor.fetchone()

    if video:
        # 确保从数据库获取的数据字段顺序正确
        video_data = {
            'id': video[0],
            'title': video[1],
            'description': video[2],
            'file_path': video[3],
            'upload_date': video[4],
            'duration': video[5],
            'like_count': video[6],
            'folder_id': folder_id[0]
        }

        # 确保 file_path 是字符串类型
        if isinstance(video_data['file_path'], str):
            video_data['video_url'] = f'/videos/{os.path.basename(video_data["file_path"])}'
            print(f"Video URL: {video_data['video_url']}")
        else:
            video_data['video_url'] = '/videos/unknown'
            print(f"Video URL (unknown): {video_data['video_url']}")

        # 如果 duration 不是数字，则设置一个默认值
        if not isinstance(video_data['duration'], (int, float)):
            video_data['duration'] = 0  # 设置默认时长为 0 秒

        return jsonify(video_data), 200
    else:
        return jsonify({"error": "Video not found"}), 404
    

@app.route('/api/like_video', methods=['POST'])
def like_video():
    video_id = request.form.get('video_id')
    ip_address = request.remote_addr  # 获取客户端IP地址
    print(f"Received request to like video with ID: {video_id} from IP: {ip_address}")
    
    if video_id is None:
        return jsonify({'success': False, 'message': 'Missing video_id'}), 400
    
    try:
        video_id = int(video_id)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid video_id'}), 400

    conn = create_connection(DATABASE)
    cursor = conn.cursor()
    
    # 检查今天是否已经点赞过
    today = datetime.utcnow().date()
    cursor.execute("""
        SELECT COUNT(*)
        FROM likes l
        WHERE l.video_id = ? AND
        DATE(l.like_date) = ?
    """, (video_id, today))
    existing_likes_today = cursor.fetchone()[0]
    
    # 检查当前IP是否已点赞
    cursor.execute("""
        SELECT COUNT(*)
        FROM likes l
        WHERE l.video_id = ? AND
        l.ip_address = ? AND
        DATE(l.like_date) = ?
    """, (video_id, ip_address, today))
    existing_likes_from_ip = cursor.fetchone()[0]
    
    if existing_likes_today >= 15:
        print(f"Daily limit reached for video ID: {video_id}")
        return jsonify({'success': False, 'message': '今日点赞次数已达上限'})
    
    if existing_likes_from_ip >= 5:
        print(f"IP daily limit reached for video ID: {video_id} and IP: {ip_address}")
        return jsonify({'success': False, 'message': '今日已点赞5次'})
    
    # 如果满足条件，则增加点赞
    cursor.execute("""
        UPDATE videos
        SET like_count = like_count + 1
        WHERE video_id = ?
    """, (video_id,))
    
    # 创建点赞记录
    cursor.execute("""
        INSERT INTO likes (video_id, ip_address, like_date)
        VALUES (?, ?, ?)
    """, (video_id, ip_address, datetime.utcnow()))
    
    conn.commit()
    
    # 获取新的点赞次数
    cursor.execute("""
        SELECT like_count
        FROM videos
        WHERE video_id = ?
    """, (video_id,))
    new_like_count = cursor.fetchone()[0]
    
    print(f"New like count for video ID: {video_id} is: {new_like_count}")
    
    return jsonify({'success': True, 'message': '点赞成功', 'new_like_count': new_like_count})


# 显示单个视频的视图函数
@app.route('/video/<int:video_id>')
def show_video(video_id):
    """显示单个视频的视图函数"""
    conn = create_connection(DATABASE)
    with conn:
        c = conn.cursor()
        c.execute("""
            SELECT title, description, duration, upload_date, file_path, like_count 
            FROM videos 
            WHERE video_id=?""", (video_id,))
        video = c.fetchone()
        if video:
            video_title, video_description, video_duration, video_upload_date, video_path, like_count = video # 查询结果解包到多个变量
            print(f"Found video: {video_title}, Path: {video_path}")  # 打印查询结果
            return render_template('video.html', 
                                   video_title=video_title, 
                                   video_description=video_description,
                                   video_duration=video_duration, 
                                   upload_date=video_upload_date, 
                                   video_path=video_path, 
                                   like_count=like_count)
        else:
            print(f"Video not found for ID: {video_id}")
            return "Video not found", 404


@app.route('/videos/<path:path>')
def serve_video(path):
    # 如果path包含"videos/"前缀，则移除它
    if path.startswith('videos/'):
        path = path[len('videos/'):]

    # 构建完整的文件路径
    full_path = os.path.join(app.config['VIDEO_FOLDER'], path)

    # 确保路径不会超出预期目录，防止路径遍历攻击
    if os.path.commonprefix([app.config['VIDEO_FOLDER'], full_path]) != app.config['VIDEO_FOLDER']:
        return "Invalid path", 403

    # 检查文件是否存在
    if os.path.exists(full_path):
        return send_from_directory(app.config['VIDEO_FOLDER'], path)
    else:
        return "File not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    print("Server started")
