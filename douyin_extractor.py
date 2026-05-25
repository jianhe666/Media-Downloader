"""Extract Douyin video info using Playwright. Outputs JSON to stdout."""

import sys, json, re, time
from playwright.sync_api import sync_playwright


def extract(url: str) -> dict | None:
    with sync_playwright() as p:
        # Try system Edge first, fall back to bundled Chromium
        for attempt, channel in enumerate(["msedge", "chrome", None]):
            try:
                if channel:
                    browser = p.chromium.launch(channel=channel, headless=True)
                else:
                    browser = p.chromium.launch(headless=True)
                break
            except Exception:
                if channel is None:
                    return {"error": "No browser available"}
                continue

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/148.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()

        video_data = {}

        def capture(response):
            if "/aweme/v1/web/aweme/detail/" in response.url and response.ok:
                try:
                    body = response.json()
                    aweme = body.get("aweme_detail", {})
                    if aweme:
                        video_data["aweme"] = aweme
                except Exception:
                    pass

        page.on("response", capture)

        try:
            # domcontentloaded fires much earlier than "load" — avoids timeout on heavy JS
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except Exception:
            pass

        # Wait for API response (poll, up to 45 seconds)
        deadline = time.time() + 45
        while not video_data and time.time() < deadline:
            page.wait_for_timeout(500)

        browser.close()

        if not video_data:
            return None

        aweme = video_data["aweme"]
        title = aweme.get("desc", "")
        duration = aweme.get("duration", 0) // 1000
        video = aweme.get("video", {})

        # Priority: play_addr (watermark-free, A+V) > play_addr_h264 > download_addr > bit_rates
        urls = video.get("play_addr", {}).get("url_list", [])
        if not urls:
            urls = video.get("play_addr_h264", {}).get("url_list", [])
        if not urls:
            urls = video.get("download_addr", {}).get("url_list", [])
        if not urls:
            bit_rates = video.get("bit_rate", [])
            if bit_rates:
                urls = bit_rates[0].get("play_addr", {}).get("url_list", [])

        if not urls:
            return None

        return {
            "title": title,
            "duration_sec": duration,
            "video_url": urls[0],
        }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: douyin_extractor.py <url>"}))
        sys.exit(1)

    try:
        result = extract(sys.argv[1])
        if result and "error" not in result:
            print(json.dumps(result, ensure_ascii=False))
        else:
            msg = result.get("error", "Failed to extract") if result else "Failed to extract"
            print(json.dumps({"error": msg}, ensure_ascii=False))
            sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(1)
