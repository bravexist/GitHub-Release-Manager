# GitHub Release Manager

一个强大的 GitHub Release 管理工具，可以自动下载和管理多个 GitHub 仓库的发布版本。

> 本项目使用 [Cursor](https://cursor.sh) 开发，并由 [Claude 3.5 Sonnet](https://www.anthropic.com/index/claude-3-sonnet-20240229) 提供智能编程支持。

## 功能特性

- 支持多仓库管理：可以同时管理多个 GitHub 仓库的发布版本
- 自动版本控制：自动保留最新的 N 个版本（可为每个仓库单独设置）
- 多线程下载：使用多线程加速下载过程
- 代理支持：支持配置代理前缀，方便国内用户使用
- 增量更新：只下载新版本，避免重复下载
- 配置持久化：使用 JSON 配置文件保存设置
- 强制更新：支持强制重新下载指定仓库的所有版本
- 序号管理：使用序号标识仓库，方便操作
- 文件完整性：自动生成文件哈希值，确保下载完整性

## 安装

### 方式一：下载可执行文件（推荐）

1. 访问 [Releases](https://github.com/bravexist/GitHub-Release-Manager/releases) 页面
2. 下载适合您系统的可执行文件：
   - Windows: `grm-windows-amd64.exe`

### 方式二：从源码安装

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

#### 使用可执行文件

```bash
# Windows
grm-windows-amd64.exe add <GitHub仓库URL> [<版本数>]    # 添加新的 GitHub 仓库，可指定保留版本数
grm-windows-amd64.exe remove <GitHub仓库URL>          # 移除已添加的仓库
grm-windows-amd64.exe update                          # 更新所有仓库的发布版本
grm-windows-amd64.exe update -f <序号>                 # 强制更新指定序号的仓库
grm-windows-amd64.exe proxy <代理前缀>                 # 设置下载代理
grm-windows-amd64.exe default-versions <版本数>        # 设置默认保留版本数
grm-windows-amd64.exe set-versions <GitHub仓库URL> <版本数> # 设置指定仓库的保留版本数
grm-windows-amd64.exe list                            # 列出所有已配置的仓库
grm-windows-amd64.exe help                            # 显示帮助信息
```

#### 从源码运行

```bash
# 使用新目录结构
python grm/main.py add <GitHub仓库URL> [<版本数>]     # 添加新的 GitHub 仓库，可指定保留版本数
python grm/main.py remove <GitHub仓库URL>           # 移除已添加的仓库
python grm/main.py update                           # 更新所有仓库的发布版本
python grm/main.py update -f <序号>                  # 强制更新指定序号的仓库
python grm/main.py proxy <代理前缀>                  # 设置下载代理
python grm/main.py default-versions <版本数>         # 设置默认保留版本数
python grm/main.py set-versions <GitHub仓库URL> <版本数> # 设置指定仓库的保留版本数
python grm/main.py list                             # 列出所有已配置的仓库
python grm/main.py help                             # 显示帮助信息

# 使用兼容模式（推荐，支持旧版本用法）
python main.py add <GitHub仓库URL> [<版本数>]        # 添加新的 GitHub 仓库，可指定保留版本数
python main.py remove <GitHub仓库URL>               # 移除已添加的仓库
python main.py update                               # 更新所有仓库的发布版本
python main.py update -f <序号>                      # 强制更新指定序号的仓库
python main.py proxy <代理前缀>                      # 设置下载代理
python main.py default-versions <版本数>             # 设置默认保留版本数
python main.py set-versions <GitHub仓库URL> <版本数>  # 设置指定仓库的保留版本数
python main.py list                                 # 列出所有已配置的仓库
python main.py help                                 # 显示帮助信息
```

### 使用示例

```bash
# 添加仓库
grm-windows-amd64.exe add https://github.com/sqlmapproject/sqlmap

# 添加仓库并指定保留5个版本
grm-windows-amd64.exe add https://github.com/sqlmapproject/sqlmap 5

# 设置代理（如果需要）
grm-windows-amd64.exe proxy https://g.bravexist.cn/

# 更新所有仓库
grm-windows-amd64.exe update

# 强制更新第一个仓库
grm-windows-amd64.exe update -f 1

# 设置默认保留3个版本
grm-windows-amd64.exe default-versions 3

# 设置特定仓库保留2个版本
grm-windows-amd64.exe set-versions https://github.com/sqlmapproject/sqlmap 2
```

## 开发者指南

### 如何发布新版本

要发布新版本并触发自动构建，请按照以下步骤操作：

1. 更新代码（如更新banner中的版本号）
2. 提交更改到仓库
   ```bash
   git add .
   git commit -m "准备发布版本 vX.Y.Z"
   ```
3. 创建新的tag
   ```bash
   git tag -a vX.Y.Z -m "版本 X.Y.Z 发布"
   ```
4. 推送tag到GitHub
   ```bash
   git push origin vX.Y.Z
   ```

推送tag后，GitHub Actions会自动触发构建流程，为Windows平台生成可执行文件，并创建发布版本。

## 配置说明

配置文件 `config.json` 包含以下设置：

- `repositories`: 要管理的仓库列表，每个仓库可以设置独立的版本数量
- `base_dir`: 下载文件的基础目录（默认为 "downloads"）
- `default_max_versions`: 每个仓库默认保留的最新版本数量（默认为 3）
- `proxy_prefix`: 下载时使用的代理前缀

## 下载目录结构

```
downloads/
├── owner1/
│   └── repo1/
│       ├── v1.0.0/
│       │   ├── asset1.zip
│       │   ├── asset2.tar.gz
│       │   └── files_info.txt
│       └── v1.1.0/
│           └── ...
└── owner2/
    └── repo2/
        └── ...
```

## 文件信息记录

每个版本目录下都会生成一个 `files_info.txt` 文件，包含以下信息：
- 文件名
- 文件大小
- 修改时间
- 文件哈希值（MD5、SHA1、SHA256、SHA512）

## 注意事项

- 确保有足够的磁盘空间存储下载的文件
- 建议定期运行 `update` 命令以获取最新版本
- 如果遇到网络问题，可以尝试设置代理
- 如果下载被中断，可以使用 `update -f` 命令强制重新下载
- 强制更新会删除已存在的版本目录，请谨慎使用

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 作者

- bravexist
