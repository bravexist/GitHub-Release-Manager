# GitHub Release Manager

一个强大的 GitHub Release 管理工具，可以自动下载和管理多个 GitHub 仓库的发布版本。

## 功能特性

- 支持多仓库管理：可以同时管理多个 GitHub 仓库的发布版本
- 自动版本控制：自动保留最新的 N 个版本（默认 3 个）
- 多线程下载：使用多线程加速下载过程
- 代理支持：支持配置代理前缀，方便国内用户使用
- 增量更新：只下载新版本，避免重复下载
- 配置持久化：使用 JSON 配置文件保存设置

## 安装

1. 克隆仓库：
```bash
git clone https://github.com/bravexist/GitHub-Release-Manager.git
cd GitHub-Release-Manager
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用方法

### 基本命令

```bash
python main.py add <GitHub仓库URL>    # 添加新的 GitHub 仓库
python main.py remove <GitHub仓库URL> # 移除已添加的仓库
python main.py update                  # 更新所有仓库的发布版本
python main.py proxy <代理前缀>         # 设置下载代理
python main.py list                    # 列出所有已配置的仓库
python main.py help                    # 显示帮助信息
```

### 示例

```bash
# 添加仓库
python main.py add https://github.com/sqlmapproject/sqlmap

# 设置代理（如果需要）
python main.py proxy https://g.bravexist.cn/

# 更新所有仓库
python main.py update
```

## 配置说明

配置文件 `config.json` 包含以下设置：

- `repositories`: 要管理的仓库列表
- `base_dir`: 下载文件的基础目录（默认为 "downloads"）
- `max_versions`: 每个仓库保留的最新版本数量（默认为 3）
- `proxy_prefix`: 下载时使用的代理前缀

## 下载目录结构

```
downloads/
├── owner1/
│   └── repo1/
│       ├── v1.0.0/
│       │   ├── asset1.zip
│       │   └── asset2.tar.gz
│       └── v1.1.0/
│           └── ...
└── owner2/
    └── repo2/
        └── ...
```

## 注意事项

- 确保有足够的磁盘空间存储下载的文件
- 建议定期运行 `update` 命令以获取最新版本
- 如果遇到网络问题，可以尝试设置代理

## 许可证

MIT License
