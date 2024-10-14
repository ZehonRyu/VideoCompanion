// 获取视频数据
function fetchVideoData(videoId) {
    fetch(`/api/video/${videoId}`)
        .then(response => response.json())
        .then(data => {
            displayVideo(data);
        })
        .catch(error => {
            console.error('Error fetching video data:', error);
        });
}

// 显示视频信息
function displayVideo(data) {
    console.log('Displaying video data:', data);

    const videoPlayer = document.getElementById('videoPlayer');
    const videoTitle = document.getElementById('videoTitle');
    const videoDescription = document.getElementById('videoDescription');
    const videoDuration = document.getElementById('videoDuration');
    const videoUploadDate = document.getElementById('videoUploadDate');
    const likeButton = document.getElementById('likeButton');
    const likeCount = document.getElementById('likeCount');
    const returnToFolderLink = document.getElementById('returnToFolder');

    if (!videoPlayer || !videoTitle || !videoDescription || !videoDuration || !videoUploadDate || !likeButton || !likeCount || !returnToFolderLink) {
        console.error('One or more DOM elements not found.');
        return;
    }

    // 确保在获取到数据后再设置视频播放器的 src
    videoPlayer.src = `/videos/${data.file_path}`; // 直接设置视频路径
    videoPlayer.load(); // 强制重新加载视频

    // 设置视频标题、描述、时长、上传时间和点赞数
    videoTitle.textContent = data.title;
    videoDescription.textContent = data.description;
    videoDuration.textContent = `视频时长：${formatDuration(data.duration)} 秒`; // 使用 formatDuration 函数格式化时长
    videoUploadDate.textContent = `上传时间：${data.upload_date}`;
    likeCount.textContent = `点赞次数：${data.like_count}`; // 确保绑定的是 like_count

    // 添加点赞按钮点击事件
    likeButton.addEventListener('click', function () {
        likeVideo(parseInt(data.id, 10)); // 使用 video_id 来点赞
    });

    // 添加返回文件夹链接点击事件
    returnToFolderLink.addEventListener('click', function (event) {
        event.preventDefault(); // 阻止默认的链接行为
        loadFolder(data.folder_id); // 加载视频所在的文件夹
    });
}

// 格式化视频时长
function formatDuration(seconds) {
    if (typeof seconds !== 'number' || isNaN(seconds)) {
        console.error('Invalid duration value:', seconds);
        return '未知';
    }
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes} 分 ${remainingSeconds.toFixed(0)} 秒`;
}

// 点赞视频
function likeVideo(videoId) {
    fetch('/api/like_video', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded', // 或 'application/json' 如果使用 JSON
        },
        body: `video_id=${videoId}` // 使用 URLSearchParams 或直接拼接字符串
    })
        .then(response => response.json())
        .then(data => {
            console.log('Data received from server:', data);
            if (data.success) {
                console.log('点赞成功');
                updateLikeCount(videoId, data.new_like_count);
            } else {
                console.error(data.message);
                alert(data.message); // 显示错误消息
            }
        })
        .catch(error => {
            console.error('Error liking video:', error);
        });
}

// 更新点赞次数
function updateLikeCount(videoId, newLikeCount) {
    const likeCount = document.getElementById('likeCount');
    if (likeCount) {
        likeCount.textContent = `点赞次数：${newLikeCount}`;
    }
}

// 初始化视频页面
function initVideoPage() {
    const videoIdFromUrl = window.location.pathname.split('/').pop();
    console.log(`Video ID from URL path: ${videoIdFromUrl}`);
    fetchVideoData(videoIdFromUrl);
}

// 加载文件夹信息
function loadFolder(folderId) {
    if (folderId) {
        window.location.href = `/folder/${folderId}`;
    } else {
        alert('无法找到视频所在的文件夹！');
    }
}


// 页面加载时初始化视频页面
document.addEventListener('DOMContentLoaded', initVideoPage);