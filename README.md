# Media Downloader

音视频下载器，基于 [yt-dlp](https://github.com/yt-dlp/yt-dlp)，支持多平台音视频下载。

## 功能

- 多平台音视频下载（Bilibili、YouTube、网易云音乐、抖音等）
- **画质手动选择**：按分辨率分级（最佳/4K/1080p/720p/480p 等）
- **音质手动选择**：按码率分级（无损 FLAC/高品 320kbps/标准 192kbps/低品 128kbps）
- 自动检测纯音频平台，切换音质选择模式
- 浏览器 Cookie 提取（Edge/Chrome/Firefox），支持登录后下载高清内容
- 抖音专用 Playwright 解析器，免登录获取无水印视频
- ffmpeg 自动下载（Release 包已附带）
- 免责声明

## 下载

最新版本：[beta V1.0.1](../../releases/tag/v1.0.1)

下载 `Media-Downloader-beta-V1.0.1.zip`，解压后运行 `Media Downloader beta V1.0.1.exe`。

## 使用

1. 粘贴视频或音频链接
2. 选择保存目录
3. 如需登录平台的高清资源，勾选「使用浏览器 Cookie」
4. 点击「开始下载」
5. 在弹出的画质/音质选择窗中选择想要的品质
6. 等待下载完成

## 免责声明

本工具仅供学习交流使用。下载内容的版权归相关权利人所有，请勿用于商业用途或未经授权的传播。使用者应确保自身行为符合相关平台的服务条款及当地法律法规。开发者不对使用本工具产生的任何后果承担责任。

## 依赖

- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [Playwright](https://playwright.dev/)（可选，用于抖音解析和 Cookie 提取）
- [FFmpeg](https://ffmpeg.org/)（Release 包已附带）

## 更新日志

详见 [CHANGELOG.md](CHANGELOG.md)
