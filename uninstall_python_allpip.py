import subprocess
import sys

def install_missing_packages():
    required_packages = ['setuptools']
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

install_missing_packages()

import pkg_resources

# 获取所有已安装的包
installed_packages = [d.project_name for d in pkg_resources.working_set]

# 卸载所有包
for package in installed_packages:
    subprocess.check_call([sys.executable, '-m', 'pip', 'uninstall', '-y', package])