# 媒达 V1.1

> 原名 Media Downloader，V1.1 起更名为"媒达"——取"媒体下载，使命必达"之意。

音视频下载器，基于 yt-dlp，支持多平台音视频下载、画质/音质手动选择。

## 功能

- 多平台音视频下载（Bilibili、YouTube、网易云音乐、抖音等）
- 画质手动选择：按分辨率分级（最佳/4K/1080p/720p/480p）
- 音质手动选择：按码率分级（无损 FLAC/高品/标准/低品）
- 自动检测纯音频平台，切换音质选择模式
- 浏览器 Cookie 自动提取（Edge/Chrome/Firefox）
- 抖音优先 Cookie，Playwright 解析兜底
- ffmpeg 内置，解压即用
- 下载进度实时显示，趣味提示语轮播

## 下载

最新版本：[V1.1](../../releases/tag/V1.1)

## 使用

1. 解压 `媒达-V1.1.zip`
2. 运行 `媒达 V1.1.exe`
3. 粘贴视频或音频链接
4. 选择保存目录
5. 点击「开始下载」
6. 在弹出的画质/音质选择窗中选择想要的品质
7. 等待下载完成

## 开发

```bash
pip install -r requirements.txt  # yt-dlp, customtkinter, playwright, requests
pyinstaller 媒达 V1.1.spec
```

## 免责声明

本工具仅供学习交流使用。下载内容的版权归相关权利人所有，请勿用于商业用途或未经授权的传播。使用者应确保自身行为符合相关平台的服务条款及当地法律法规。

## 更新日志

详见 [CHANGELOG.md](CHANGELOG.md)
