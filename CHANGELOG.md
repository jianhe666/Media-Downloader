# Media Downloader

音视频下载器，基于 yt-dlp，支持多平台音视频下载、画质/音质手动选择。

## beta V1.0.1 (2026-05-25)

- 修复 ffmpeg 下载失败问题：增加国内镜像源（ghproxy），优先查找 exe 同目录下的 ffmpeg 文件
- ffmpeg 文件随 Release 包一起分发，无需在线下载

## beta V1.0.0 (2026-05-25)

- 首次发布
- 支持多平台音视频下载（yt-dlp）
- 支持画质手动选择（按分辨率分级：最佳/2160p/1080p/720p/480p 等）
- 支持音质手动选择（按码率分级：无损/高品/标准/低品，支持 FLAC 检测）
- 自动检测纯音频平台（如网易云音乐），切换音质选择模式
- 支持浏览器 Cookie 提取（Edge/Chrome/Firefox）
- 抖音专用 Playwright 解析器
- ffmpeg 自动下载
- 首次启动免责声明
