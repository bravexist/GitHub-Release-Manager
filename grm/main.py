import os
import json
import requests
import time
import shutil
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor
import sys
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urlparse
import hashlib
from datetime import datetime

def print_banner():
    banner = """
    ╔════════════════════════════════════════════════════════════════════════════╗
    ║                                                                           ║
    ║   ██████╗ ██╗████████╗██╗   ██╗██████╗ ███████╗██╗     ███████╗███████╗  ║
    ║  ██╔════╝ ██║╚══██╔══╝██║   ██║██╔══██╗██╔════╝██║     ██╔════╝██╔════╝  ║
    ║  ██║  ███╗██║   ██║   ██║   ██║██████╔╝█████╗  ██║     █████╗  ███████╗  ║
    ║  ██║   ██║██║   ██║   ╚██╗ ██╔╝██╔══██╗██╔══╝  ██║     ██╔══╝  ╚════██║  ║
    ║  ╚██████╔╝██║   ██║    ╚████╔╝ ██║  ██║███████╗███████╗███████╗███████║  ║
    ║   ╚═════╝ ╚═╝   ╚═╝     ╚═══╝  ╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝╚══════╝  ║
    ║                                                                           ║
    ║  GitHub Release Manager - 强大的 GitHub Release 管理工具                 ║
    ║  Version: 0.0.7                                                          ║
    ║  Author: bravexist                                                       ║
    ║                                                                           ║
    ╚════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GithubReleaseUpdater:
    def __init__(self, config_path="config.json"):
        """初始化 GitHub Release 更新器"""
        self.config_path = config_path
        self.config = self._load_config()
        self.base_dir = Path(self.config.get("base_dir", "downloads"))
        self.max_versions = self.config.get("max_versions", 3)
        self.proxy_prefix = self.config.get("proxy_prefix", "")
        self.max_retries = 3  # 最大重试次数
        self.retry_delay = 5  # 重试延迟（秒）
        
        # 配置 requests 会话
        self.session = requests.Session()
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
    def _load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # 如果配置文件不存在，创建默认配置
            default_config = {
                "repositories": [],
                "base_dir": "downloads",
                "max_versions": 3,
                "proxy_prefix": ""
            }
            self._save_config(default_config)
            return default_config
    
    def _save_config(self, config=None):
        """保存配置到文件"""
        if config is None:
            config = self.config
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    
    def add_repository(self, owner, repo):
        """添加新的仓库到配置"""
        repo_info = {"owner": owner, "repo": repo}
        if repo_info not in self.config["repositories"]:
            self.config["repositories"].append(repo_info)
            self._save_config()
            logger.info(f"已添加仓库: {owner}/{repo}")
        else:
            logger.info(f"仓库已存在: {owner}/{repo}")
    
    def remove_repository(self, owner, repo):
        """从配置中移除仓库"""
        repo_info = {"owner": owner, "repo": repo}
        if repo_info in self.config["repositories"]:
            self.config["repositories"].remove(repo_info)
            self._save_config()
            logger.info(f"已移除仓库: {owner}/{repo}")
        else:
            logger.info(f"仓库不存在: {owner}/{repo}")
    
    def set_proxy_prefix(self, prefix):
        """设置代理前缀"""
        self.config["proxy_prefix"] = prefix
        self.proxy_prefix = prefix
        self._save_config()
        logger.info(f"已设置代理前缀: {prefix}")
    
    def get_releases(self, owner, repo):
        """获取仓库的发布版本信息"""
        url = f"https://api.github.com/repos/{owner}/{repo}/releases"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"获取 {owner}/{repo} 的发布版本失败: {e}")
            return []
    
    def download_asset(self, url, save_path):
        """下载资源文件"""
        # 处理代理前缀
        if self.proxy_prefix:
            parsed_url = urlparse(url)
            if parsed_url.netloc == "api.github.com":
                # 对于 GitHub API 的请求，不使用代理
                download_url = url
            else:
                # 对于其他下载链接，使用代理
                download_url = f"{self.proxy_prefix}{url}"
        else:
            download_url = url
            
        retry_count = 0
        
        while retry_count < self.max_retries:
            try:
                response = self.session.get(download_url, stream=True)
                response.raise_for_status()
                
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                logger.info(f"下载完成: {save_path}")
                return True
            except requests.RequestException as e:
                retry_count += 1
                if retry_count < self.max_retries:
                    logger.warning(f"下载失败，{retry_count}/{self.max_retries} 次重试: {url}")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"下载失败 {url}: {e}")
                    return False
    
    def process_release(self, owner, repo, release, force=False):
        """处理单个发布版本"""
        version = release["tag_name"]
        release_dir = self.base_dir / owner / repo / version
        
        # 检查是否已下载，如果已存在且不是强制更新，则跳过
        if release_dir.exists() and not force:
            logger.info(f"版本已存在: {owner}/{repo}/{version}")
            return
        
        # 如果是强制更新且目录已存在，先删除旧目录
        if force and release_dir.exists():
            logger.info(f"强制更新: 删除旧版本 {owner}/{repo}/{version}")
            shutil.rmtree(release_dir)
        
        os.makedirs(release_dir, exist_ok=True)
        
        # 使用多线程下载所有资源
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            
            # 下载发布资源
            for asset in release["assets"]:
                asset_path = release_dir / asset["name"]
                futures.append(executor.submit(
                    self.download_asset, 
                    asset["browser_download_url"], 
                    asset_path
                ))
            
            # 下载源代码包
            if "zipball_url" in release:
                zip_path = release_dir / f"{repo}-{version}-source.zip"
                futures.append(executor.submit(
                    self.download_asset,
                    release["zipball_url"],
                    zip_path
                ))
            
            if "tarball_url" in release:
                tar_path = release_dir / f"{repo}-{version}-source.tar.gz"
                futures.append(executor.submit(
                    self.download_asset,
                    release["tarball_url"],
                    tar_path
                ))
            
            # 等待所有下载完成
            for future in futures:
                future.result()
        
        # 生成文件信息记录
        self.generate_file_info(str(release_dir))
    
    def get_directory_size(self, path):
        """计算目录大小"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        return total_size
    
    def format_size(self, size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"
    
    def update_repository(self, owner, repo, force=False):
        """更新单个仓库的发布版本"""
        logger.info(f"正在检查 {owner}/{repo} 的更新...")
        releases = self.get_releases(owner, repo)
        
        if not releases:
            logger.info(f"没有找到 {owner}/{repo} 的发布版本")
            return
        
        # 获取已下载的版本
        repo_dir = self.base_dir / owner / repo
        existing_versions = []
        if repo_dir.exists():
            existing_versions = [d.name for d in repo_dir.iterdir() if d.is_dir()]
        
        # 获取GitHub上所有版本的标签
        all_versions = [release["tag_name"] for release in releases]
        
        # 找出需要下载的新版本
        versions_to_download = []
        for release in releases:
            version = release["tag_name"]
            if force or version not in existing_versions:
                versions_to_download.append(release)
        
        # 确定要保留的版本（最新的max_versions个）
        versions_to_keep = all_versions[:self.max_versions]
        
        # 下载需要的新版本
        if versions_to_download:
            # 只下载需要保留的版本中尚未下载的部分
            versions_to_actually_download = [r for r in versions_to_download if r["tag_name"] in versions_to_keep]
            if versions_to_actually_download:
                logger.info(f"将为 {owner}/{repo} 下载 {len(versions_to_actually_download)} 个新版本")
                with ThreadPoolExecutor(max_workers=3) as executor:
                    for release in versions_to_actually_download:
                        executor.submit(self.process_release, owner, repo, release, force)
            else:
                logger.info(f"没有新版本需要下载: {owner}/{repo}")
        else:
            logger.info(f"没有新版本需要下载: {owner}/{repo}")
        
        # 不删除已存在的旧版本，确保有最新的max_versions个版本即可
        logger.info(f"保留 {owner}/{repo} 的所有已下载版本")
    
    def update_all(self, force_repo_index=None):
        """更新所有配置的仓库"""
        if force_repo_index is not None:
            # 强制更新指定序号的仓库
            if 1 <= force_repo_index <= len(self.config["repositories"]):
                repo_info = self.config["repositories"][force_repo_index - 1]
                self.update_repository(repo_info["owner"], repo_info["repo"], force=True)
            else:
                logger.error(f"无效的仓库序号: {force_repo_index}")
        else:
            # 正常更新所有仓库
            with ThreadPoolExecutor(max_workers=5) as executor:
                for repo_info in self.config["repositories"]:
                    owner = repo_info["owner"]
                    repo = repo_info["repo"]
                    executor.submit(self.update_repository, owner, repo)
    
    def parse_github_url(self, url):
        """从GitHub URL中解析出所有者和仓库名"""
        # 匹配格式: https://github.com/owner/repo 或 github.com/owner/repo
        pattern = r'(?:https?://)?(?:www\.)?github\.com/([^/]+)/([^/]+)'
        match = re.match(pattern, url)
        if match:
            return match.group(1), match.group(2)
        return None, None
    
    def list_repositories(self):
        """列出所有仓库及其版本信息"""
        print("\n已配置的仓库:")
        print("-" * 80)
        for idx, repo_info in enumerate(self.config["repositories"], 1):
            owner = repo_info["owner"]
            repo = repo_info["repo"]
            repo_dir = self.base_dir / owner / repo
            
            print(f"[{idx}] 仓库: {owner}/{repo}")
            if repo_dir.exists():
                versions = [d.name for d in repo_dir.iterdir() if d.is_dir()]
                total_size = self.get_directory_size(repo_dir)
                print(f"    版本数量: {len(versions)}")
                print(f"    总大小: {self.format_size(total_size)}")
                print(f"    版本列表: {', '.join(versions)}")
                if versions:
                    latest_version = versions[0]  # 假设版本按时间倒序排列
                    latest_path = repo_dir / latest_version
                    if latest_path.exists():
                        print(f"    最新版本: {latest_version} -> {latest_path}")
            else:
                print("    尚未下载任何版本")
            print("-" * 80)

    def calculate_file_hashes(self, file_path):
        """计算文件的多种哈希值"""
        hashes = {}
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
                hashes['md5'] = hashlib.md5(data).hexdigest()
                hashes['sha1'] = hashlib.sha1(data).hexdigest()
                hashes['sha256'] = hashlib.sha256(data).hexdigest()
                hashes['sha512'] = hashlib.sha512(data).hexdigest()
        except Exception as e:
            logger.error(f"计算文件哈希值时出错 {file_path}: {e}")
        return hashes

    def generate_file_info(self, directory):
        """生成目录下所有文件的信息记录"""
        info = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file == "files_info.txt":  # 跳过信息文件本身
                    continue
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, directory)
                file_size = os.path.getsize(file_path)
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                hashes = self.calculate_file_hashes(file_path)
                
                info.append({
                    "文件名": relative_path,
                    "大小": self.format_size(file_size),
                    "修改时间": file_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "哈希值": hashes
                })
        
        # 将信息写入文件
        info_file = os.path.join(directory, "files_info.txt")
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write("文件信息记录\n")
            f.write("=" * 50 + "\n\n")
            for item in info:
                f.write(f"文件名: {item['文件名']}\n")
                f.write(f"大小: {item['大小']}\n")
                f.write(f"修改时间: {item['修改时间']}\n")
                f.write("哈希值:\n")
                for hash_type, hash_value in item['哈希值'].items():
                    f.write(f"  {hash_type}: {hash_value}\n")
                f.write("-" * 50 + "\n")

def print_usage():
    """打印使用说明"""
    print("使用方法:")
    print("  python main.py add <GitHub仓库URL>    - 添加GitHub仓库")
    print("  python main.py remove <GitHub仓库URL> - 移除GitHub仓库")
    print("  python main.py update                 - 更新所有仓库")
    print("  python main.py update -f <序号>        - 强制更新指定序号的仓库")
    print("  python main.py proxy <代理前缀>        - 设置代理前缀")
    print("  python main.py list                   - 列出所有仓库")
    print("  python main.py help                   - 显示帮助信息")
    print("\n示例:")
    print("  python main.py add https://github.com/sqlmapproject/sqlmap")
    print("  python main.py proxy https://g.bravexist.cn/")
    print("  python main.py update -f 1            - 强制更新第一个仓库")

def main():
    if len(sys.argv) < 2:
        print_banner()
        print_usage()
        return

    updater = GithubReleaseUpdater()
    command = sys.argv[1]

    if command == "add":
        if len(sys.argv) != 3:
            print("错误：请提供 GitHub 仓库 URL")
            return
        owner, repo = updater.parse_github_url(sys.argv[2])
        updater.add_repository(owner, repo)
    elif command == "remove":
        if len(sys.argv) != 3:
            print("错误：请提供 GitHub 仓库 URL")
            return
        owner, repo = updater.parse_github_url(sys.argv[2])
        updater.remove_repository(owner, repo)
    elif command == "update":
        force_repo_index = None
        if len(sys.argv) > 2 and sys.argv[2] == "-f":
            if len(sys.argv) != 4:
                print("错误：请提供要强制更新的仓库序号")
                return
            try:
                force_repo_index = int(sys.argv[3])
            except ValueError:
                print("错误：仓库序号必须是数字")
                return
        updater.update_all(force_repo_index)
    elif command == "proxy":
        if len(sys.argv) != 3:
            print("错误：请提供代理前缀")
            return
        updater.set_proxy_prefix(sys.argv[2])
    elif command == "list":
        updater.list_repositories()
    elif command == "help":
        print_banner()
        print_usage()
    else:
        print("错误：未知命令")
        print_usage()

if __name__ == "__main__":
    main()
