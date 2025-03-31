import os
import hashlib
from datetime import datetime
from pathlib import Path
import argparse

def format_size(size):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

def calculate_file_hashes(file_path):
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
        print(f"计算文件哈希值时出错 {file_path}: {e}")
    return hashes

def generate_file_info(directory):
    """生成目录下所有文件的信息记录"""
    directory = Path(directory)
    if not directory.exists():
        print(f"目录不存在: {directory}")
        return
    
    info = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file == "files_info.txt":  # 跳过信息文件本身
                continue
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, directory)
            file_size = os.path.getsize(file_path)
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            hashes = calculate_file_hashes(file_path)
            
            info.append({
                "文件名": relative_path,
                "大小": format_size(file_size),
                "修改时间": file_time.strftime("%Y-%m-%d %H:%M:%S"),
                "哈希值": hashes
            })
    
    # 将信息写入文件
    info_file = directory / "files_info.txt"
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
    
    print(f"已生成文件信息记录: {info_file}")

def process_directory(directory, recursive=False):
    """处理目录，可选择是否递归处理子目录"""
    directory = Path(directory)
    if not directory.exists():
        print(f"目录不存在: {directory}")
        return
    
    # 处理当前目录
    print(f"\n处理目录: {directory}")
    generate_file_info(directory)
    
    # 如果启用递归，处理所有子目录
    if recursive:
        for item in directory.iterdir():
            if item.is_dir():
                process_directory(item, recursive=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='生成文件信息记录工具')
    parser.add_argument('directory', help='要处理的目录路径')
    parser.add_argument('-r', '--recursive', action='store_true', help='递归处理所有子目录')
    
    args = parser.parse_args()
    
    process_directory(args.directory, args.recursive) 