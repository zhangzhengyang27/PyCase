# -*- coding: utf-8 -*-
import sys, argparse, traceback, importlib

'''
Job 统一入口文件
python manager.py runjob -m Test ( 运行的是 jobs/tasks/Test.py )
python manager.py runjob -m test/index ( 运行的是 jobs/tasks/test/index.py )
'''


def runJob(args = None):
    if args is None:
        args = sys.argv[2:] # 获取参数
    parser = argparse.ArgumentParser(add_help=True)  # 创建解析对象
    parser.add_argument("-m", "--name", dest="name", metavar="name", help="指定 job 名", required=True)
    parser.add_argument("-a", "--act", dest="act", metavar="act", help="Job 动作", required=False)
    # nargs="*" 表示可接受多个参数
    parser.add_argument("-p", "--param", dest="param", nargs="*", metavar="param", help="业务参数",
                        required=False)  # 非必须参数
    params = parser.parse_args(args)  # 解析参数
    params_dict = params.__dict__  # 转换为字典

    if "name" not in params_dict or not params_dict['name']:
        return tips()  # 提示

    try:
        '''
        from jobs.tasks.test import JobTask
        '''
        module_name = params_dict['name'].replace("/", ".") # 替换路径
        import_string = "jobs.tasks.%s" % (module_name) # 拼接路径
        target = importlib.import_module(import_string) # 导入模块
        exit(target.JobTask().run(params_dict)) # 执行任务
    except Exception as e:
        traceback.print_exc()
    return


def tips():
    tip_msg = '''
    请正确的调度Job
    python manager.py runjob -m Test ( jobs/tasks/Test.py )
    python manager.py runjob -m test/index ( jobs/tasks/test/index.py )
    '''
    print(tip_msg)
    return
