import subprocess
import sys

def install_missing_packages():
    required_packages = ['GPUtil', 'setuptools', 'distutils']
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

install_missing_packages()

try:
    import GPUtil
except ImportError:
    print("Error: GPUtil 模块未找到，请确保已安装 GPUtil。")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'GPUtil'])
    import GPUtil

import os
import tkinter as tk
from tkinter import filedialog
import json

def process_single_file(input_file_path, output_file_path, index):
    file_size = os.path.getsize(input_file_path)
    print(f"\n[文件序号: {index}] {os.path.basename(input_file_path)} ({file_size} 字节)")
    print(f"输入文件路径: {input_file_path}")
    print(f"输出文件路径: {output_file_path}")

    # 二进制读取文件
    with open(input_file_path, 'rb') as f:
        file_bytes = f.read()

    if len(file_bytes) > 200:
        prefix_bytes = file_bytes[:200]
        rest_bytes = file_bytes[200:]
    else:
        prefix_bytes = file_bytes
        rest_bytes = b''

    # 去掉前导 '0' (仅限前 200 字节部分)
    trimmed_bytes = prefix_bytes.lstrip(b'0')
    new_bytes = trimmed_bytes + rest_bytes

    with open(output_file_path, 'wb') as f:
        f.write(new_bytes)
    new_file_size = os.path.getsize(output_file_path)
    print(f"生成: {os.path.basename(output_file_path)} ({new_file_size} 字节, 差异: {file_size - new_file_size} 字节)")

def get_gpu_info():
    # 优先通过 dxdiag 获取详细的 GPU 信息
    try:
        temp_file = os.path.join(os.path.dirname(__file__), 'dxdiag_info.txt')
        subprocess.run(["dxdiag", "/t", temp_file], check=True)
        gpu_name = None

        with open(temp_file, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            for line in lines:
                if "Card name:" in line:
                    gpu_name = line.split("Card name:")[1].strip()
                    break

        if gpu_name:
            return gpu_name
    except:
        pass

    # 如果 dxdiag 未成功，则继续尝试使用现有 GPUtil 方式
    try:
        gpus = GPUtil.getGPUs()
        if not gpus:
            raise Exception("GPUtil 未检测到 GPU")
        return gpus[0].name
    except Exception as e:
        print(f"GPUtil 获取 GPU 信息时发生错误: {e}")
        try:
            result = subprocess.run(['wmic', 'path', 'win32_videocontroller', 'get', 'name'], capture_output=True, text=True)
            if result.returncode == 0:
                gpu_info = result.stdout.split('\n')[1].strip()
                if (gpu_info):
                    return gpu_info
            return None
        except Exception as e:
            print(f"subprocess 获取 GPU 信息时发生错误: {e}")
            return None

def get_video_title(video_folder_path):
    video_info_path = os.path.join(video_folder_path, 'videoInfo.json')
    if os.path.exists(video_info_path):
        try:
            with open(video_info_path, 'r', encoding='utf-8') as f:
                video_info = json.load(f)
                return video_info.get('title', None)
        except Exception as e:
            print(f"读取 videoInfo.json 文件时发生错误: {e}")
            return None
    return None

def sanitize_path(path):
    # 去除双引号，仅保留斜杠替换
    return path.replace('\\', '/')

def sanitize_filename(filename):
    return "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_', '~')).rstrip()

def process_video_files(video_folder_path, output_folder_path, output_filename, gpu_name):
    # 保留用户选择的输出文件夹
    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path)
        print(f"创建输出文件夹: {output_folder_path}")

    # 获取文件夹中的所有 m4s 文件
    m4s_files = sorted([f for f in os.listdir(video_folder_path) if f.endswith('.m4s')], key=lambda x: os.path.getsize(os.path.join(video_folder_path, x)))
    print(f"找到 {len(m4s_files)} 个 m4s 文件")

    # 初始化 ffmpeg 参数列表
    ffmpeg_arguments = []

    # 遍历每个 m4s 文件并进行处理
    temp_output_files = []
    for index, m4s_file in enumerate(m4s_files, start=1):
        input_file_path = os.path.join(video_folder_path, m4s_file)
        temp_output_file = os.path.join(video_folder_path, f"{index}.temp.m4s")
        process_single_file(input_file_path, temp_output_file, index)
        temp_output_files.append(temp_output_file)
        ffmpeg_arguments.extend(['-i', sanitize_path(temp_output_file)])

    sanitized_output_filename = sanitize_filename(output_filename)
    final_output_path = sanitize_path(os.path.join(output_folder_path, sanitized_output_filename + ".mp4"))
    ffmpeg_arguments.extend(['-threads', '4'])

    if gpu_name:
        gpu_name_lower = gpu_name.lower()
        if 'nvidia' in gpu_name_lower:
            ffmpeg_arguments.extend(['-c:v', 'h264_nvenc'])
        elif 'intel' in gpu_name_lower:
            ffmpeg_arguments.extend(['-c:v', 'h264_qsv'])
        elif 'amd' in gpu_name_lower or 'radeon' in gpu_name_lower:
            ffmpeg_arguments.extend(['-c:v', 'h264_amf'])
        else:
            ffmpeg_arguments.extend(['-c:v', 'libx264'])
    else:
        ffmpeg_arguments.extend(['-c:v', 'libx264'])

    ffmpeg_arguments.extend(['-codec', 'copy', final_output_path])
    print(f"使用的 GPU: {gpu_name if gpu_name else '无'}")
    print(f"ffmpeg 参数: {' '.join(ffmpeg_arguments)}")

    script_dir = os.path.abspath(os.path.dirname(__file__))
    ffmpeg_path = os.path.join(script_dir, 'ffmpeg.exe')
    if not os.path.isfile(ffmpeg_path):
        print("Error: 未在脚本所在目录找到 ffmpeg.exe，请将其放在相同文件夹下后重试。")
        return

    result = subprocess.run(
        [ffmpeg_path] + ffmpeg_arguments,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    if result.returncode != 0:
        print(f"ffmpeg 错误: {result.stderr}")
    else:
        print("视频处理完成!")

    # 删除临时文件
    for temp_output_file in temp_output_files:
        if os.path.exists(temp_output_file):
            os.remove(temp_output_file)
            print(f"已删除临时文件: {temp_output_file}")

def get_subfolders(parent_folder_path):
    return [os.path.join(parent_folder_path, name) for name in os.listdir(parent_folder_path) if os.path.isdir(os.path.join(parent_folder_path, name))]

if __name__ == "__main__":
    try:
        print("程序启动...")

        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口

        gpu_name = get_gpu_info()
        print(f"检测到的 GPU: {gpu_name}")

        print("正在选择父级文件夹路径...")
        parent_folder_path = filedialog.askdirectory(title="请选择包含视频文件夹的父级文件夹路径")
        if not parent_folder_path:
            print("未选择文件夹")
            input("按任意键退出...")
            exit()
        print(f"选择的父级文件夹路径: {parent_folder_path}")

        chosen_folder_paths = get_subfolders(parent_folder_path)
        if not chosen_folder_paths:
            print("父级文件夹中没有子文件夹")
            input("按任意键退出...")
            exit()
        print(f"找到的子文件夹路径:")
        for folder_path in chosen_folder_paths:
            print(folder_path)

        print("正在选择输出文件夹路径...")
        chosen_output_folder_path = filedialog.askdirectory(title="请选择要保存输出文件的文件夹路径")
        if not chosen_output_folder_path:
            chosen_output_folder_path = parent_folder_path
        print(f"选择的输出文件夹路径: {chosen_output_folder_path}")

        for folder_path in chosen_folder_paths:
            video_title = get_video_title(folder_path)
            if not video_title:
                video_title = os.path.basename(os.path.normpath(folder_path))
            output_filename = video_title
            print(f"保存文件名: {output_filename}.mp4")
            process_video_files(folder_path, chosen_output_folder_path, output_filename, gpu_name)

        input("处理完成，按任意键结束...")
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
        input("按任意键退出...")
