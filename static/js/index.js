let currentFolderId = null; // 用于存储当前文件夹ID
let parentFolderId = null; // 用于存储父文件夹ID

// 初始化函数
function init() {
    // 加载当前文件夹的信息
    loadCurrentFolder();

    // 监听排序按钮点击事件
    document.querySelectorAll('.sort-button').forEach(button => { // . 是class
        button.addEventListener('click', function () {
            sortVideos(this.dataset.sort);
        });
    });

    // 监听返回根目录链接点击事件
    document.getElementById('goToRootFolder').addEventListener('click', function (event) { // id = goToRootFolder
        event.preventDefault(); // 阻止默认的链接行为
        loadCurrentFolder(null); // 加载根目录
    });

    // 添加加载子文件夹的事件监听器
    document.getElementById('subFolders').addEventListener('click', function(event) {
        if (event.target.tagName.toLowerCase() === 'a') { //如果用户点击了一个链接，event.target 就是那个链接元素。event.target.tagName：获取目标元素的标签名
            event.preventDefault(); // 阻止默认的链接行为，跳转url
            loadCurrentFolder(event.target.dataset.folderId); // 加载子文件夹
        }
    });

    // 添加前往父文件夹链接的点击事件
    document.getElementById('goToParentFolder').addEventListener('click', function (event) {
        event.preventDefault(); // 阻止默认的链接行为
        loadCurrentFolder(parentFolderId); // 加载父文件夹
    });
}

// 加载当前文件夹的信息
function loadCurrentFolder(folderId) {
    currentFolderId = folderId; // 保存当前文件夹ID
    fetch(`/api/current_folder?folder_id=${folderId || ''}`)
        .then(response => response.json())
        .then(data => {
            displayFolder(data);
        })
        .catch(error => {
            console.error('Error fetching folder data:', error);
        });
}

// 显示文件夹信息
function displayFolder(data) {
    console.log('Displaying folder data:', data);

    // 确保元素存在
    const currentFolderNameElement = document.getElementById('currentFolderName');
    const subFoldersElement = document.getElementById('subFolders');
    const videoListElement = document.getElementById('videoList');
    const goToParentFolderElement = document.getElementById('goToParentFolder');

    if (!currentFolderNameElement || !subFoldersElement || !videoListElement || !goToParentFolderElement) {
        console.error('One or more DOM elements not found.');
        return;
    }

    currentFolderNameElement.textContent = data.name;

    // 清空子文件夹列表
    subFoldersElement.innerHTML = '';

    // 添加子文件夹链接
    data.subFolders.forEach(subFolder => {
        const li = document.createElement('li');
        const link = document.createElement('a');
        link.href = '#'; // 使用 # 避免实际跳转
        link.textContent = subFolder.name;
        link.dataset.folderId = subFolder.id; // 添加数据属性
        li.appendChild(link);
        subFoldersElement.appendChild(li);
    });

    // 清空视频列表
    videoListElement.querySelector('tbody').innerHTML = '';

    // 添加视频列表
    data.videos.forEach(video => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><a href="/video/${video.video_id}" target="_blank">${video.title}</a></td>
            <td>${video.like_count}</td>
            <td>${video.duration} 秒</td>
            <td>${video.upload_date}</td>
        `;
        videoListElement.querySelector('tbody').appendChild(row);
    });

    // 设置前往父文件夹链接的可见性和ID
    goToParentFolderElement.style.display = data.parentId ? 'inline' : 'none';
    parentFolderId = data.parentId; // 保存父文件夹ID

    // 调试输出
    console.log('Current folder ID:', currentFolderId);
    console.log('Parent folder ID:', parentFolderId);
    console.log('Go to parent folder element visibility:', goToParentFolderElement.style.display);
    console.log('Go to parent folder element:', goToParentFolderElement);

    // 添加前往父文件夹链接的点击事件
    goToParentFolderElement.addEventListener('click', function (event) {
        event.preventDefault(); // 阻止默认的链接行为
        loadCurrentFolder(parentFolderId); // 加载父文件夹
    });
}

// 排序视频列表
function sortVideos(sortType) {
    fetch(`/api/sorted_videos?sort=${sortType}&folder_id=${currentFolderId}`)
        .then(response => response.json())
        .then(data => {
            displayFolder(data);
        })
        .catch(error => {
            console.error('Error fetching sorted videos:', error);
        });
}

// 页面加载完成时初始化
document.addEventListener('DOMContentLoaded', init);