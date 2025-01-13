# bilibilim4stomp4
B站（bilibili）本地缓存批量转mp4格式，GPU加速

# 平台限制
1. 仅支持windows使用
2. 需要自行安装python 3
3. 需要安装pip，会自动安装缺失的依赖，请保证网络畅通
4. 由于github对大文件限制，ffmpeg需要自行解压到代码目录

# 使用方法
1. 使用B站App缓存需要转换的视频，例如 `d:\bilibili`
2. 运行 `bilibili_m4s2mp4.py`，选择B站缓存目录，会自动获取所有子文件夹的缓存文件，选择转换后视频的保存目录

# 实现逻辑
1. 遍历每个缓存目录，把文件前置的0去掉，另存为 temp.m4s
2. 调用dxdiag判断显卡内存，增加相关ffmpeg.exe 参数
3. 调用ffmpeg.exe 转换视频
