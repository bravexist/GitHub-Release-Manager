import os
import json
import requests
import time
import shutil
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor

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
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"获取 {owner}/{repo} 的发布版本失败: {e}")
            return []
    
    def download_asset(self, url, save_path):
        """下载资源文件"""
        download_url = f"{self.proxy_prefix}{url}" if self.proxy_prefix else url
        try:
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"下载完成: {save_path}")
            return True
        except requests.RequestException as e:
            logger.error(f"下载失败 {url}: {e}")
            return False
    
    def process_release(self, owner, repo, release):
        """处理单个发布版本"""
        version = release["tag_name"]
        release_dir = self.base_dir / owner / repo / version
        
        # 检查是否已下载
        if release_dir.exists():
            logger.info(f"版本已存在: {owner}/{repo}/{version}")
            return
        
        os.makedirs(release_dir, exist_ok=True)
        
        # 下载所有资源
        for asset in release["assets"]:
            asset_path = release_dir / asset["name"]
            self.download_asset(asset["browser_download_url"], asset_path)
    
    def update_repository(self, owner, repo):
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
        
        # 首次执行时下载最新版本，之后执行时只下载新版本
        if not existing_versions:
            # 首次执行，只下载最新版本
            logger.info(f"首次执行，下载 {owner}/{repo} 的最新版本")
            self.process_release(owner, repo, releases[0])
        else:
            # 之后执行，下载所有新版本
            logger.info(f"检查 {owner}/{repo} 的新版本")
            for release in releases:
                version = release["tag_name"]
                if version not in existing_versions:
                    logger.info(f"发现新版本: {owner}/{repo}/{version}")
                    self.process_release(owner, repo, release)
    
    def update_all(self):
        """更新所有配置的仓库"""
        with ThreadPoolExecutor(max_workers=5) as executor:
            for repo_info in self.config["repositories"]:
                owner = repo_info["owner"]
                repo = repo_info["repo"]
                executor.submit(self.update_repository, owner, repo)

if __name__ == "__main__":
    updater = GithubReleaseUpdater()
    
    # 示例：添加仓库
    updater.add_repository("SleepingBag945", "dddd")
    
    # 示例：设置代理前缀（如果在中国大陆访问GitHub较慢，可以使用代理）
    updater.set_proxy_prefix("https://g.bravexist.cn/")
    
    # 示例：设置下载目录和保留版本数量
    updater.config["base_dir"] = "downloads"
    updater.config["max_versions"] = 5
    updater._save_config()
    
    # 更新所有仓库
    updater.update_all()
    
    # 完整使用示例
    """
    # 初始化更新器
    updater = GithubReleaseUpdater()
    
    # 添加要监控的仓库
    updater.add_repository("SleepingBag945", "dddd")
    
    # 设置代理前缀（可选）
    updater.set_proxy_prefix("https://g.bravexist.cn/")
    
    # 更新所有仓库
    updater.update_all()
    
    # 下载的文件将保存在 downloads/SleepingBag945/dddd/[版本号] 目录下
    """
