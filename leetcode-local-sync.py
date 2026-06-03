#!/usr/bin/env python3
"""
LeetCode 本地同步脚本
自动从浏览器读取 Cookie（避免手动提取）
支持多语言解答
自动根据语言类型生成正确的注释格式
文件夹命名：0001-two-sum 格式
"""

import os
import sys
import json
import sqlite3
import requests
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import subprocess

class LeetCodeLocalSync:
    def __init__(self, output_dir: str = "solutions"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 获取 Cookie
        self.session_token, self.csrf_token = self.get_cookies()
        
        if not self.session_token:
            print("❌ 无法获取 Cookie")
            print("   请按以下步骤操作：")
            print("   1. 在 LeetCode 网页上登录")
            print("   2. 按 F12 → Application → Cookies → https://leetcode.com")
            print("   3. 复制 LEETCODE_SESSION 和 csrftoken 的值")
            print("   4. 创建文件 ./.leetcode_cookies.json，内容：")
            print('      {"session": "你的session值", "csrf": "你的csrf值"}')
            sys.exit(1)
    
    def get_cookies(self) -> tuple:
        """获取 Cookie（优先配置文件，其次浏览器）"""
        # 方法1：从配置文件读取
        config_path = Path.cwd() / ".leetcode_cookies.json"
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    cookies = json.load(f)
                    session = cookies.get('session') or cookies.get('LEETCODE_SESSION')
                    csrf = cookies.get('csrf') or cookies.get('csrftoken')
                    if session and csrf:
                        print("✅ 从配置文件读取 Cookie")
                        return session, csrf
            except Exception as e:
                print(f"⚠️ 读取配置文件失败: {e}")
        
        # 方法2：从浏览器读取（Windows）
        cookie_paths = [
            os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Cookies"),
            os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\Cookies"),
        ]
        
        for cookie_path in cookie_paths:
            if os.path.exists(cookie_path):
                print(f"🔍 尝试读取: {cookie_path}")
                try:
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
                    temp_file.close()
                    shutil.copy2(cookie_path, temp_file.name)
                    
                    conn = sqlite3.connect(temp_file.name)
                    cursor = conn.cursor()
                    
                    cursor.execute(
                        "SELECT value FROM cookies WHERE host_key LIKE '%leetcode.com%' AND name='LEETCODE_SESSION'"
                    )
                    session_row = cursor.fetchone()
                    
                    cursor.execute(
                        "SELECT value FROM cookies WHERE host_key LIKE '%leetcode.com%' AND name='csrftoken'"
                    )
                    csrf_row = cursor.fetchone()
                    
                    conn.close()
                    os.unlink(temp_file.name)
                    
                    if session_row and csrf_row:
                        print("✅ 从浏览器读取 Cookie")
                        return session_row[0], csrf_row[0]
                except Exception as e:
                    print(f"⚠️ 读取失败: {e}")
        
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
    
    def format_folder_name(self, submission: Dict) -> str:
        """格式化文件夹名称：0001-two-sum（使用 question_id）"""
        question_id = submission.get('question_id', 0)
        title_slug = submission['title_slug']
        
        try:
            problem_id = int(question_id)
            folder_name = f"{problem_id:04d}-{title_slug}"
        except (ValueError, TypeError):
            folder_name = f"0000-{title_slug}"
        
        return folder_name
    
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
    
    def generate_header(self, submission: Dict) -> str:
        """根据语言生成对应的注释头部"""
        title = submission['title']
        title_slug = submission['title_slug']
        lang = submission['lang']
        question_id = submission.get('question_id', 0)
        timestamp = int(submission['timestamp'])
        date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        
        # 显示带编号的标题
        display_title = f"[{question_id:04d}] {title}" if question_id else title
        
        info_lines = [
            f"LeetCode: {display_title}",
            f"Link: https://leetcode.com/problems/{title_slug}/",
            f"Date: {date_str}",
            f"Language: {lang}",
            "Status: Accepted"
        ]
        
        # Python
        if lang in ['python', 'python3', 'py']:
            return '"""\n' + '\n'.join(info_lines) + '\n"""\n\n'
        
        # JavaScript / TypeScript / Java / C / C++ / C# / Go / Rust / Swift / Kotlin
        elif lang in ['javascript', 'js', 'typescript', 'ts', 'java', 'cpp', 'c', 'csharp', 'cs', 'go', 'rust', 'rs', 'swift', 'kotlin', 'kt']:
            return '/**\n * ' + '\n * '.join(info_lines) + '\n */\n\n'
        
        # Ruby
        elif lang in ['ruby', 'rb']:
            return '\n'.join([f"# {line}" for line in info_lines]) + "\n\n"
        
        # 默认
        else:
            return '\n'.join([f"# {line}" for line in info_lines]) + "\n\n"
    
    def save_solution(self, submission: Dict) -> bool:
        """保存解答，返回是否保存了新文件"""
        title_slug = submission['title_slug']
        lang = submission['lang']
        
        # 使用 question_id 生成文件夹名
        folder_name = self.format_folder_name(submission)
        
        # 创建题目目录（使用带编号的文件夹名）
        problem_dir = self.output_dir / folder_name
        problem_dir.mkdir(exist_ok=True)
        
        # 文件名：solution.py, solution.js, solution.java 等
        ext = self.get_file_extension(lang)
        filename = f'solution{ext}'
        filepath = problem_dir / filename
        
        # 如果文件已存在，跳过
        if filepath.exists():
            return False
        
        # 生成正确的注释头部
        header = self.generate_header(submission)
        
        # 写入文件
        filepath.write_text(header + submission['code'], encoding='utf-8')
        print(f"✅ 新增: {folder_name}/{filename}")
        return True
    
    def generate_readme(self, submissions: List[Dict]) -> None:
        """生成 README（按编号排序）"""
        problems = {}
        for sub in submissions:
            slug = sub['title_slug']
            lang = self.normalize_language(sub['lang'])
            question_id = int(sub.get('question_id', 0))
            
            if slug not in problems:
                problems[slug] = {
                    'id': question_id,
                    'title': sub['title'],
                    'languages': set()
                }
            problems[slug]['languages'].add(lang)
        
        # 按编号排序
        sorted_problems = sorted(problems.values(), key=lambda x: x['id'])
        
        readme = f"""# LeetCode Solutions

> 自动同步脚本 | 最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 统计

- 总题数: **{len(problems)}**
- 总解答数: **{len(submissions)}**

## 题目列表

| 编号 | 题目 | 语言 |
|------|------|------|
"""
        
        for info in sorted_problems:
            # 找到对应的 slug
            slug = [k for k, v in problems.items() if v['id'] == info['id']][0] if info['id'] > 0 else ''
            langs = ', '.join(sorted(info['languages']))
            readme += f"| {info['id']:04d} | [{info['title']}](https://leetcode.com/problems/{slug}/) | {langs} |\n"
        
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