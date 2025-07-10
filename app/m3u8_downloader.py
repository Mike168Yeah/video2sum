#!/usr/bin/env python3
import sys
import os
import subprocess
import requests
import m3u8
from pathlib import Path
import argparse
import time
import tempfile
import json
from typing import List, Optional, Dict, Union
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import urllib.parse
import re
from tqdm import tqdm

class M3U8Downloader:
    def __init__(self, user_agent: Optional[str] = None, referer: Optional[str] = None):
        """初始化下載器"""
        self.user_agent = user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        self.referer = referer or 'https://gdcvault.com/'
        self.headers = {
            'User-Agent': self.user_agent,
            'Referer': self.referer
        }

    def _extract_gdc_id(self, url: str) -> Optional[str]:
        """從 URL 中提取 GDC ID"""
        if 'gdcvault.blazestreaming.com' in url:
            parsed = urllib.parse.urlparse(url)
            query = urllib.parse.parse_qs(parsed.query)
            return query.get('id', [None])[0]
        else:
            match = re.search(r'/play/(\d+)/', url)
            if match:
                return match.group(1)
        return None

    def _get_urls_with_requests(self, url: str) -> List[str]:
        """使用 requests 方式獲取串流 URL"""
        try:
            # 從 URL 提取 ID
            gdc_id = self._extract_gdc_id(url)
            if not gdc_id:
                print("無法從 URL 提取 GDC ID")
                return []

            # 構建 iframe URL
            iframe_url = f"https://gdcvault.blazestreaming.com/?id={gdc_id}"
            response = requests.get(iframe_url, headers=self.headers)
            response.raise_for_status()
            
            print("回應狀態:", response.status_code)
            print("內容類型:", response.headers.get('content-type'))
            
            # 使用多種正則表達式尋找可能的影片來源
            patterns = [
                r'https?://[^\s<>"]+?\.m3u8',  # 標準 m3u8
                r'https?://[^\s<>"]+?\.mp4',    # MP4
                r'"url":"(https?://[^"]+?\.m3u8)"',  # JSON 中的 m3u8
                r'source:\s*["\']([^"\']+?\.m3u8)["\']',  # JavaScript 中的 m3u8
                r'playlist:\s*["\']([^"\']+?\.m3u8)["\']'  # 播放列表中的 m3u8
            ]
            
            for pattern in patterns:
                urls = re.findall(pattern, response.text)
                if urls:
                    print(f"使用模式 {pattern} 找到的 URLs:")
                    for found_url in urls:
                        print(found_url)
                    return urls

            print("\n頁面內容片段:")
            print(response.text[:1000])
                    
            return []
        except Exception as e:
            print(f"使用 requests 方式失敗: {str(e)}")
            return []

    def _get_urls_with_selenium(self, url: str) -> List[str]:
        """使用 Selenium 獲取串流 URL"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--log-level=3')
        options.add_argument('--enable-javascript')
        
        driver = None
        try:
            service = Service()
            driver = webdriver.Chrome(options=options, service=service)
            
            print(f"訪問頁面: {url}")
            driver.get(url)
            
            print("等待頁面載入...")
            time.sleep(5)

            # 獲取所有 cookies
            cookies = driver.get_cookies()
            cookie_string = '; '.join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
            
            # 尋找 iframe 中的播放器
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            if iframes:
                print(f"找到 {len(iframes)} 個 iframe")
                for idx, iframe in enumerate(iframes):
                    try:
                        print(f"檢查 iframe {idx + 1}")
                        driver.switch_to.frame(iframe)
                        
                        # 檢查播放器腳本
                        scripts = driver.find_elements(By.TAG_NAME, "script")
                        for script in scripts:
                            src = script.get_attribute('src')
                            if src and ('script_VOD.js' in src or 'player.js' in src):
                                print("找到播放器腳本")
                                # 嘗試從不同的變數中獲取 URL
                                possible_vars = [
                                    "window.PLAYBACK_URL",
                                    "window.playbackUrl",
                                    "window.videoUrl",
                                    "window.streamUrl"
                                ]
                                
                                for var in possible_vars:
                                    try:
                                        playback_url = driver.execute_script(f"return {var};")
                                        if playback_url and isinstance(playback_url, str):
                                            print(f"找到播放 URL: {playback_url}")
                                            return [playback_url]
                                    except:
                                        continue
                        
                        # 檢查播放器元素
                        video_elements = driver.find_elements(By.TAG_NAME, "video")
                        for video in video_elements:
                            src = video.get_attribute('src')
                            if src and ('.m3u8' in src or '.mp4' in src):
                                print(f"在 video 元素中找到視頻源: {src}")
                                return [src]
                        
                        # 檢查 video.js 播放器
                        video_js = driver.find_elements(By.CLASS_NAME, "video-js")
                        for player in video_js:
                            for attr in ['data-setup', 'data-sources']:
                                try:
                                    data = player.get_attribute(attr)
                                    if data:
                                        sources = json.loads(data)
                                        if isinstance(sources, dict) and 'sources' in sources:
                                            urls = [s['src'] for s in sources['sources'] if 'src' in s]
                                            if urls:
                                                print(f"在 video.js 播放器中找到視頻源:")
                                                for url in urls:
                                                    print(url)
                                                return urls
                                except:
                                    continue
                                    
                    except Exception as e:
                        print(f"處理 iframe {idx + 1} 時發生錯誤: {str(e)}")
                    finally:
                        driver.switch_to.parent_frame()
            
            # 如果在 iframe 中沒有找到，檢查主頁面
            print("檢查主頁面...")
            page_source = driver.page_source
            patterns = [
                r'https?://[^\s<>"]+?\.m3u8',
                r'https?://[^\s<>"]+?\.mp4',
                r'"url":"(https?://[^"]+?\.m3u8)"',
                r'source:\s*["\']([^"\']+?\.m3u8)["\']',
                r'playlist:\s*["\']([^"\']+?\.m3u8)["\']',
                r'PLAYBACK_URL\s*=\s*["\']([^"\']+)["\']',
                r'playbackUrl\s*=\s*["\']([^"\']+)["\']',
                r'videoUrl\s*=\s*["\']([^"\']+)["\']',
                r'streamUrl\s*=\s*["\']([^"\']+)["\']'
            ]
            
            all_urls = []
            for pattern in patterns:
                urls = re.findall(pattern, page_source)
                if urls:
                    print(f"\n使用模式 {pattern} 找到的 URLs:")
                    for url in urls:
                        if isinstance(url, tuple):
                            url = url[0]
                        if '.m3u8' in url or '.mp4' in url:
                            print(url)
                            all_urls.append(url)
            
            if all_urls:
                return list(set(all_urls))
            
            print("\n在頁面中沒有找到媒體 URL")
            return []
            
        except Exception as e:
            print(f"使用 selenium 方式失敗: {str(e)}")
            return []
        finally:
            if driver:
                driver.quit()

    def get_stream_urls(self, url: str, method: str = 'requests') -> List[str]:
        """獲取影片串流網址"""
        found_urls = []
        
        if method in ['requests', 'both']:
            print("\n使用 requests 方式尋找:")
            urls = self._get_urls_with_requests(url)
            found_urls.extend(urls)
        
        if method in ['selenium', 'both'] and not found_urls:
            print("\n使用 selenium 方式尋找:")
            urls = self._get_urls_with_selenium(url)
            found_urls.extend(urls)
        
        return list(set(found_urls))

    def download_audio(self, url: str, output_path: str, format: str = 'mp3', quality: Union[int, str] = 4) -> bool:
        """下載音頻（加上進度條）"""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            # 先取得 m3u8 檔案所有分段
            m3u8_obj = m3u8.load(url)
            segments = m3u8_obj.segments
            if not segments:
                print("無法取得 m3u8 分段，將直接用 ffmpeg 下載（無進度條）")
                return self._ffmpeg_download(url, output_path, format, quality)
            # 逐段下載
            temp_dir = tempfile.mkdtemp()
            segment_files = []
            for i, seg in enumerate(tqdm(segments, desc="下載分段", unit="段")):
                if isinstance(seg.uri, str):
                    seg_path = os.path.join(temp_dir, f"seg_{i}.ts")
                    r = requests.get(seg.uri, headers=self.headers, stream=True)
                    with open(seg_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    segment_files.append(seg_path)
            # 合併分段
            if segment_files:
                concat_file = os.path.join(temp_dir, "concat.txt")
                with open(concat_file, 'w') as f:
                    for seg_file in segment_files:
                        f.write(f"file '{seg_file}'\n")
                cmd = [
                    'ffmpeg', '-f', 'concat', '-safe', '0', '-i', concat_file,
                    '-c:a', 'libmp3lame' if format.lower() == 'mp3' else 'aac',
                    '-q:a', str(quality) if format.lower() == 'mp3' else '-b:a', '192k',
                    '-y', output_path
                ]
                print(f"合併分段並轉檔到: {output_path}")
                subprocess.run(cmd, check=True)
                print("音頻下載完成！")
                return True
            else:
                print("沒有可用的分段檔案，下載失敗。")
                return False
        except Exception as e:
            print(f"下載過程中發生錯誤: {str(e)}")
            return False

    def _ffmpeg_download(self, url, output_path, format, quality):
        cmd = [
            'ffmpeg',
            '-headers', f'Referer: {self.headers["Referer"]}\r\nUser-Agent: {self.headers["User-Agent"]}\r\n',
            '-i', url,
            '-vn'
        ]
        if format.lower() == 'mp3':
            cmd.extend(['-c:a', 'libmp3lame', '-q:a', str(quality)])
        else:
            cmd.extend(['-c:a', 'aac', '-b:a', '192k'])
        cmd.extend(['-y', output_path])
        print(f"開始下載音頻到: {output_path}")
        proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True)
        pbar = None
        try:
            for line in proc.stderr:
                if 'Duration:' in line:
                    dur = line.split('Duration:')[1].split(',')[0].strip()
                    h, m, s = dur.split(':')
                    total_sec = int(h)*3600 + int(m)*60 + float(s)
                    pbar = tqdm(total=total_sec, desc="ffmpeg 下載進度", unit="秒")
                if 'time=' in line and pbar:
                    t = line.split('time=')[1].split(' ')[0]
                    h, m, s = t.split(':')
                    cur_sec = int(h)*3600 + int(m)*60 + float(s)
                    pbar.n = int(cur_sec)
                    pbar.refresh()
            proc.wait()
            if pbar:
                pbar.close()
            if proc.returncode == 0:
                print("音頻下載完成！")
                return True
            else:
                print("下載失敗！")
                return False
        except Exception as e:
            if pbar:
                pbar.close()
            print(f"下載過程中發生錯誤: {str(e)}")
            return False

    def download_video(self, url: str, output_path: str) -> bool:
        """下載完整影片（加上進度條）"""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            # 直接用 ffmpeg 下載，並加上進度條
            return self._ffmpeg_download(url, output_path, 'mp4', 4)
        except Exception as e:
            print(f"下載過程中發生錯誤: {str(e)}")
            return False

def main():
    parser = argparse.ArgumentParser(description='M3U8 串流下載工具')
    parser.add_argument('url', help='影片網址')
    parser.add_argument('--output', '-o', required=True, help='輸出檔案路徑')
    parser.add_argument('--method', choices=['requests', 'selenium', 'both'], 
                      default='both', help='URL 獲取方法 (預設: both)')
    parser.add_argument('--type', choices=['video', 'audio'], 
                      default='video', help='下載類型 (預設: video)')
    parser.add_argument('--format', choices=['mp3', 'aac'], 
                      default='mp3', help='音訊格式 (僅用於音訊下載, 預設: mp3)')
    parser.add_argument('--quality', type=int, default=4,
                      help='MP3 音質等級 0-9 (僅用於 MP3, 預設: 4)')
    
    args = parser.parse_args()
    
    # 建立下載器實例
    downloader = M3U8Downloader()
    
    # 獲取串流 URL
    print(f"正在獲取串流網址: {args.url}")
    urls = downloader.get_stream_urls(args.url, method=args.method)
    
    if not urls:
        print("未找到任何串流網址")
        sys.exit(1)
    
    # 使用最後一個 URL（通常是最高品質）
    stream_url = urls[-1]
    print(f"\n使用串流網址: {stream_url}")
    
    # 根據類型執行下載
    if args.type == 'audio':
        success = downloader.download_audio(
            stream_url, 
            args.output,
            format=args.format,
            quality=args.quality
        )
    else:
        success = downloader.download_video(stream_url, args.output)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
