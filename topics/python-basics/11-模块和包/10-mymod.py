def print_me():
    print('me')


# print_me()

# 调用演示（原 mod_test.py）：
# import mymod
# mymod.print_me()

# 参考：https://www.python.org/dev/peps/pep-0008/

# PyCharm 配置 autopep8：
# cmd 窗口输入：pip install autopep8
# Tools → External Tools → 点击加号
# Name：Autopep8（可以随便取）
# - Tools settings:
#     - Programs：autopep8 （前提是你已经安装了哦）
#     - Parameters：--in-place --aggressive --aggressive $FilePath$
#     - Working directory：$ProjectFileDir$
# - 点击 Output Filters → 添加，在对话框中的 Regular expression to match output
#   中输入：$FILE_PATH$\:$LINE$\:$COLUMN$\:.*

