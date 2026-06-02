#!/usr/bin/env python3
"""
LeetCode 本地同步脚本
自动从浏览器读取 Cookie（避免手动提取）
支持多语言解答
"""

import os
import sys
import json
import sqlite3
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import subprocess

class LeetCodeLocalSync:
    def __init__(self, output_dir: str = "solutions"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 自动从浏览器获取 Cookie
        self.session_token, self.csrf_token = self.get_cookies_from_browser()
        
        if not self.session_token:
            print("❌ 无法自动获取 Cookie，请手动登录 LeetCode 后重试")
            sys.exit(1)
    
    def get_cookies_from_browser(self) -> tuple:
        """从本地浏览器（Chrome/Edge）自动读取 LeetCode Cookie"""
        
        # Chrome/Edge 的 Cookie 数据库路径
        cookie_paths = [
            os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/Cookies"),  # macOS Chrome
            os.path.expanduser("~/Library/Application Support/Google/Chrome/Profile 1/Cookies"),
            os.path.expanduser("~/AppData/Local/Google/Chrome/User Data/Default/Cookies"),  # Windows Chrome
            os.path.expanduser("~/snap/chromium/common/chromium/Default/Cookies"),  # Linux
        ]
        
        for cookie_path in cookie_paths:
            if os.path.exists(cookie_path):
                try:
                    # 复制 Cookie 文件（避免锁定）
                    import tempfile, shutil
                    temp_cookie = tempfile.NamedTemporaryFile(delete=False)
                    shutil.copy2(cookie_path, temp_cookie.name)
                    
                    # 连接 SQLite 数据库
                    conn = sqlite3.connect(temp_cookie.name)
                    cursor = conn.cursor()
                    
                    # 查询 LEETCODE_SESSION
                    cursor.execute(
                        "SELECT value FROM cookies WHERE host_key LIKE '%leetcode.com%' AND name='LEETCODE_SESSION'"
                    )
                    session_row = cursor.fetchone()
                    
                    # 查询 csrftoken
                    cursor.execute(
                        "SELECT value FROM cookies WHERE host_key LIKE '%leetcode.com%' AND name='csrftoken'"
                    )
                    csrf_row = cursor.fetchone()
                    
                    conn.close()
                    os.unlink(temp_cookie.name)
                    
                    if session_row and csrf_row:
                        print("✅ 成功从浏览器读取 Cookie")
                        return session_row[0], csrf_row[0]
                        
                except Exception as e:
                    print(f"⚠️ 读取 Cookie 失败: {e}")
                    continue
        
        # 如果自动读取失败，尝试从配置文件读取
        config_path = Path.home() / ".leetcode_cookies.json"
        if config_path.exists():
            with open(config_path) as f:
                cookies = json.load(f)
                return cookies.get('session'), cookies.get('csrf')
        
        return None, None
    
    def fetch_submissions(self, limit: int = 50) -> List[Dict]:
        """获取最近的通过记录"""
        headers = {
            'Cookie': f'LEETCODE_SESSION={self.session_token}; csrftoken={self.csrf_token}',
            'x-csrftoken': self.csrf_token,
            'Referer': 'https://leetcode.com/',
            'Content-Type': 'application/json',
        }
        
        url = f'https://leetcode.com/api/submissions/?offset=0&limit={limit}'
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ API 请求失败: {response.status_code}")
            if response.status_code == 401:
                print("   Cookie 可能已过期，请重新登录 LeetCode 并运行脚本")
            return []
        
        data = response.json()
        submissions = data.get('submissions_dump', [])
        accepted = [s for s in submissions if s.get('status_display') == 'Accepted']
        
        # 去重：每个题目每种语言只保留最新的一条
        latest = {}
        for sub in accepted:
            key = f"{sub['title_slug']}_{sub['lang']}"
            if key not in latest or int(sub['timestamp']) > int(latest[key]['timestamp']):
                latest[key] = sub
        
        return list(latest.values())
    
    def normalize_language(self, lang: str) -> str:
        """标准化语言名称"""
        lang_map = {
            'python3': 'py',
            'python': 'py',
            'javascript': 'js',
            'typescript': 'ts',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'csharp': 'cs',
            'go': 'go',
            'rust': 'rs',
            'ruby': 'rb',
            'swift': 'swift',
            'kotlin': 'kt',
        }
        return lang_map.get(lang, lang)
    
    def get_file_extension(self, lang: str) -> str:
        """获取文件扩展名"""
        ext_map = {
            'py': '.py',
            'js': '.js',
            'ts': '.ts',
            'java': '.java',
            'cpp': '.cpp',
            'c': '.c',
            'cs': '.cs',
            'go': '.go',
            'rs': '.rs',
            'rb': '.rb',
            'swift': '.swift',
            'kt': '.kt',
        }
        normalized = self.normalize_language(lang)
        return ext_map.get(normalized, f'.{normalized}')
    
    def save_solution(self, submission: Dict) -> bool:
        """保存解答，返回是否保存了新文件"""
        title_slug = submission['title_slug']
        lang = submission['lang']
        lang_normalized = self.normalize_language(lang)
        
        # 创建题目目录
        problem_dir = self.output_dir / title_slug
        problem_dir.mkdir(exist_ok=True)
        
        # 文件名：solution.py, solution.js, solution.java 等
        ext = self.get_file_extension(lang)
        filename = f'solution{ext}'
        filepath = problem_dir / filename
        
        # 如果文件已存在，跳过
        if filepath.exists():
            return False
        
        # 添加元数据头部
        timestamp = int(submission['timestamp'])
        header = f'''"""
LeetCode: {submission['title']}
Link: https://leetcode.com/problems/{title_slug}/
Date: {datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')}
Language: {lang}
Status: Accepted
"""

'''
        
        # 写入文件
        filepath.write_text(header + submission['code'], encoding='utf-8')
        print(f"✅ 新增: {title_slug}/{filename}")
        return True
    
    def generate_readme(self, submissions: List[Dict]) -> None:
        """生成 README"""
        problems = {}
        for sub in submissions:
            slug = sub['title_slug']
            lang = self.normalize_language(sub['lang'])
            if slug not in problems:
                problems[slug] = {
                    'title': sub['title'],
                    'languages': set()
                }
            problems[slug]['languages'].add(lang)
        
        readme = f"""# LeetCode Solutions

> 自动同步脚本 | 最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 统计

- 总题数: **{len(problems)}**
- 总解答数: **{len(submissions)}**

## 题目列表

| 题目 | 语言 |
|------|------|
"""
        
        for slug, info in sorted(problems.items()):
            langs = ', '.join(sorted(info['languages']))
            readme += f"| [{info['title']}](https://leetcode.com/problems/{slug}/) | {langs} |\n"
        
        readme += f"\n---\n*Powered by LeetCode Local Sync*\n"
        
        (self.output_dir / 'README.md').write_text(readme, encoding='utf-8')
        print("✅ 更新 README.md")
    
    def git_commit_and_push(self) -> None:
        """自动 commit 并 push 到 GitHub"""
        try:
            # 检查是否有变更
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.output_dir.parent,
                capture_output=True,
                text=True
            )
            
            if not result.stdout.strip():
                print("📝 没有新变更，跳过提交")
                return
            
            # git add
            subprocess.run(['git', 'add', '.'], cwd=self.output_dir.parent, check=True)
            
            # git commit
            commit_msg = f"Sync LeetCode solutions - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            subprocess.run(['git', 'commit', '-m', commit_msg], cwd=self.output_dir.parent, check=True)
            print(f"✅ 提交成功: {commit_msg}")
            
            # git push
            subprocess.run(['git', 'push'], cwd=self.output_dir.parent, check=True)
            print("✅ 推送成功到 GitHub")
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Git 操作失败: {e}")
    
    def run(self) -> None:
        print("🚀 开始同步 LeetCode 解答...")
        
        submissions = self.fetch_submissions()
        if not submissions:
            print("⚠️ 没有获取到通过记录，请检查网络或 Cookie")
            return
        
        print(f"📊 找到 {len(submissions)} 个通过记录（去重后）")
        return
        
        new_count = 0
        for sub in submissions:
            if self.save_solution(sub):
                new_count += 1
        
        if new_count > 0:
            self.generate_readme(submissions)
            self.git_commit_and_push()
            print(f"✨ 同步完成！新增 {new_count} 个解答")
        else:
            print("📭 没有新解答需要同步")

if __name__ == '__main__':
    syncer = LeetCodeLocalSync()
    syncer.run()