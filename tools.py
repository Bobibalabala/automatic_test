import os
import unittest
import sys
import csv
import subprocess
import socket
import threading
import time
import requests
import json
import datetime
from io import StringIO

HEADERS = {'Authorization': 'Bearer {token}', "Accept": "application/vnd.ceph.api.v1.0+json"}
URL = "http://{}/api/"


def get_func_print(func, *args, **kwargs):
    """有些接口只是打印，需要根据打印结果来判断执行是否正常，这里返回函数执行中print的结果"""
    output = StringIO()
    sys.stdout = output
    func(*args, **kwargs)
    print_info = output.getvalue()
    sys.stdout = sys.__stdout__
    return print_info

def get_cmd_print(cmd):
    """获取命令执行后的输出"""
    p = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
    stdout, stderr = p.communicate()
    stdout = stdout.decode('utf-8', errors='replace') if isinstance(stdout, bytes) else stdout
    stderr = stderr.decode('utf-8', errors='replace') if isinstance(stderr, bytes) else stderr
    return stdout if stdout else stderr


def get_shell_cmd_result(cmd):
    """获取shell命令的结果，如ls -a"""
    p = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
    stdout, stderr = p.communicate()
    stdout = stdout.decode('utf-8', errors='replace') if isinstance(stdout, bytes) else stdout
    stderr = stderr.decode('utf-8', errors='replace') if isinstance(stderr, bytes) else stderr
    return stdout, stderr, p.returncode


def get_local_ip():
    """获取本地节点的IP地址"""
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    return ip


def get_local_hostname():
    return socket.gethostname()


def get_remote_hostname(ip):
    return socket.gethostbyaddr(ip)


def get_ip_by_name(name):
    return socket.gethostbyname(name)


def get_datetime_str(fmt="%Y-%m-%d", delta_type="days", delta_num=10):
    """
    获取时间格式的字符串
    fmt: 输出格式
    delta_type: 偏差时间类型
    delta_type: 偏差时间数量
    """
    now = datetime.datetime.now()
    if delta_type == 'weeks':
        delta = datetime.timedelta(weeks=delta_num)
    elif delta_type == 'days':
        delta = datetime.timedelta(days=delta_num)
    elif delta_type == 'minutes':
        delta = datetime.timedelta(minutes=delta_num)
    elif delta_type == 'seconds':
        delta = datetime.timedelta(seconds=delta_num)
    else:
        delta = datetime.timedelta(weeks=0)

    return (now + delta).strftime(fmt)

def get_workdir():
    """获取当前的工作目录"""
    basedir = os.path.dirname(__file__)
    return basedir


def get_test_config_path():
    """返回用于存放测试过程中产生的测试文件以及测试的配置文件的路径"""
    dirname = 'configs'
    wdir = get_workdir()
    path = wdir + '/' + dirname
    if not os.path.exists(path):
        os.mkdir(path)
    return path


def get_test_configuration_path():
    """用于返回测试用的总的配置文件的路径"""
    basedir = get_workdir()
    return basedir + '/configuration.txt'


class ResultRecord:
    """对excel工作簿中指定的工作表进行操作"""
    def __init__(self, filename):
        self.fieldnames = ['序号', '描述', '命令', '结果', '备注']
        self.filename = filename
        if os.path.exists(self.filename):
            pass
        else:
            with open(self.filename, 'w', newline='', encoding='utf-8-sig') as f:
                csv_writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                csv_writer.writeheader()
        self.file_hander = open(self.filename, 'a', newline='', encoding='utf-8-sig')
        self.csv_writer = csv.DictWriter(self.file_hander, fieldnames=self.fieldnames)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.file_hander.close()
        pass         

    def write_row(self, row):
        """写一行数据, row是字典形式的"""
        self.csv_writer.writerow(row)

    def truncate(self):
        """删除表中的内容，保留表头"""
        with open(self.filename, 'w', newline='', encoding='utf-8-sig') as f:
            csv_writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            csv_writer.writeheader()


class MyTextTestResult(unittest.TextTestResult):
    """显示测试执行结果的类，重写定制以符合自身要求的显示效果"""
    # 记录当前用例的序号以及描述
    test_order = {'序号': '', '描述': ''}
    separator3 = ' ' * 70
    basedir = os.path.dirname(__file__)
    # 执行用例时产生的日志目录
    logs_dir = "logs"
    # 执行用例后的结果目录
    result_dir = "result_csv"
    log_basedir = basedir + f'/{logs_dir}'
    csv_basedir = basedir + f'/{result_dir}'
    for d in [log_basedir, csv_basedir]:
        if not os.path.exists(d):
            os.mkdir(d)
    log_path = log_basedir + '/' + os.path.basename(sys.argv[0]).split('.')[0] + '.log' if sys.argv[0] else 'test_cmd.log'
    csv_file = csv_basedir + '/' + os.path.basename(sys.argv[0]).split('.')[0] + '.csv'
    with open(log_path, 'w') as f:
        pass
    with ResultRecord(csv_file) as cf:
        cf.truncate()

    def write_csv(self, info):
        """信息写到csv中, info是字典类型"""
        with ResultRecord(self.csv_file) as cf:
            cf.write_row(info)

    def getDescription(self, test):
        doc_first_line = test.shortDescription()
        if doc_first_line:
            return doc_first_line
        else:
            return str(test)
        
    def printErrorList(self, flavour, errors):
        for test, err in errors:
            self.stream.writeln(self.separator1)
            self.stream.writeln('\033[31m{}: \033[0m{}'.format(self.getDescription(test), flavour))
            err = err.strip()
            errinfo = '\n'.join(err.split(' : ', 1))
            self.stream.writeln("%s" % errinfo)
            self.stream.writeln(self.separator3)

    def err_format(self, errinfo):
        return '\n'.join(errinfo.split(' : '))
    
    def startTest(self, test):
        order = '###' + str(self.testsRun + 1)
        test_name = self.getDescription(test)
        if self.showAll:
            self.stream.write(order+'  ')
        self.test_order = {'序号': order, '描述': test_name}
        with open(self.log_path, 'a') as f:
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write('=' * 35 + r"[   Start   {}  at  {}  ]".format(test_name, now) + '=' * 35 + '\n')
        super(MyTextTestResult, self).startTest(test)

    def write_log(self, test):

        with open(self.log_path, 'r') as f:
            org_content = f.read()
        if not os.path.exists("/var/log/messages"):  # 如果在windos上运行的话不记录日志
            return
        update_log_content = get_shell_cmd_result('tail -n 30 /var/log/messages')
        logsinfo = update_log_content[0].splitlines()
        with open(self.log_path, 'a') as f:
            test_name = self.getDescription(test)
            for item in logsinfo:
                item = item.strip()
                if item and item not in org_content:
                    f.write(item+'\n')
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write('=' * 35 + r"[   End   {}  at  {}  ]".format(test_name, now) + '=' * 35 + '\n')
            f.write('\n')

    def addSuccess(self, test):
        super(MyTextTestResult, self).addSuccess(test)
        self.write_log(test)
        if self.showAll:
            if hasattr(test, 'now_cmd') and test.now_cmd:
                self.stream.writeln(test.now_cmd)
                infos = {'命令': test.now_cmd.split('\r\b')[-1], '结果': 'ok'}
                infos.update(self.test_order)
                self.write_csv(infos)
            self.stream.writeln('')

    def addError(self, test, err):
        super(MyTextTestResult, self).addError(test, err)
        self.write_log(test)
        if self.showAll:
            if hasattr(test, 'now_cmd') and test.now_cmd:
                self.stream.writeln(f'\033[31m{test.now_cmd}\033[0m')
                errinfo = self._exc_info_to_string(err, test)
                infos = {'命令': test.now_cmd.split('\r\b')[-1], '结果': 'error', '备注': errinfo.strip()}
                infos.update(self.test_order)
                self.write_csv(infos)
            self.stream.writeln('')

    def addFailure(self, test, err):
        super(MyTextTestResult, self).addFailure(test, err)
        self.write_log(test)
        if self.showAll:
            if hasattr(test, 'now_cmd') and test.now_cmd:
                self.stream.writeln(f'\033[31m{test.now_cmd}\033[0m')
                errinfo = self._exc_info_to_string(err, test)
                infos = {'命令': test.now_cmd.split('\r\b')[-1], '结果': 'fail', '备注': errinfo.strip()}
                infos.update(self.test_order)
                self.write_csv(infos)
            self.stream.writeln('')

    def addSkip(self, test, reason):
        super(MyTextTestResult, self).addSkip(test, reason)
        if self.showAll:
            if hasattr(test, 'now_cmd') and test.now_cmd:
                self.stream.writeln(test.now_cmd)
                infos = {'命令': test.now_cmd.split('\r\b')[-1], '结果': 'skip', '备注': reason}
                infos.update(self.test_order)
                self.write_csv(infos)
            self.stream.writeln('')

    def addExpectedFailure(self, test, err):
        super(MyTextTestResult, self).addExpectedFailure(test, err)
        self.write_log(test)
        if self.showAll:
            if hasattr(test, 'now_cmd') and test.now_cmd:
                self.stream.writeln(test.now_cmd)
                errinfo = self._exc_info_to_string(err, test)
                infos = {'命令': test.now_cmd.split('\r\b')[-1], '结果': 'exceptfailure', '备注': errinfo.strip()}
                infos.update(self.test_order)
                self.write_csv(infos)
            self.stream.writeln('')

    def addUnexpectedSuccess(self, test):
        super(MyTextTestResult, self).addUnexpectedSuccess(test)
        self.write_log(test)
        if self.showAll:
            if hasattr(test, 'now_cmd') and test.now_cmd:
                self.stream.writeln(test.now_cmd)
                infos = {'命令': test.now_cmd.split('\r\b')[-1], '结果': 'unexpectedsuccess'}
                infos.update(self.test_order)
                self.write_csv(infos)
            self.stream.writeln('')


class MyTextTestRunner(unittest.TextTestRunner):
    """测试运行器，设置我们定制好的结果显示器"""

    def __init__(self, stream=None, descriptions=True, verbosity=1,
                 failfast=False, buffer=False, resultclass=None, warnings=None,
                 *, tb_locals=False):
        super().__init__(stream=stream, descriptions=descriptions, verbosity=verbosity, failfast=failfast,
                         buffer=buffer, resultclass=MyTextTestResult, warnings=warnings, tb_locals=tb_locals)
        

class MyTestLoader(unittest.TestLoader):
    """这是加载测试用例的类，将以下参数设置为None可以让每一类的测试用例能不必排序"""
    def __init__(self):
        super().__init__()
        self.sortTestMethodsUsing = None


class MyTestCase(unittest.TestCase):
    # 用于记录当前测试的命令
    now_cmd = '\r\b'
    token = None

    def get_cmd_print(self, cmd):
        """设置now_cmd并返回命令执行的结果"""
        self.now_cmd += '\n' + ' ' * 6 + cmd
        return get_cmd_print(cmd)
    
    def GET(self, url):
        self.now_cmd += '\n' + ' ' * 6 + 'GET ' + url
        return GuiRequest(self.token).GET(url)

    def POST(self, url, data=None, timeout=60):
        """timeout: 请求发起到最多等待获取最后结果的时间"""
        self.now_cmd += '\n' + ' ' * 6 + 'POST ' + url
        return GuiRequest(self.token).POST(url, data=data)

    def PUT(self, url, data=None):
        self.now_cmd += '\n' + ' ' * 6 + 'PUT ' + url
        return GuiRequest(self.token).PUT(url, data=data)

    def DELETE(self, url, data=None):
        self.now_cmd += '\n' + ' ' * 6 + 'DELETE ' + url
        return GuiRequest(self.token).DELETE(url, data=data)

    def assertOPsuccess(self, result):
        """对于操作类的请求由其请求值判断操作是否成功"""
        ret = result[0]
        err = result[1]
        self.assertFalse(ret, msg=f"操作结果失败: {err}")


class DefaultConfig:
    """测试执行前，获取的一些配置信息"""
    configpath = get_test_configuration_path()
    if not os.path.exists(configpath):
        config_test = {'config1': 'c1', 'config2': 'c2'}
        conf = {'config_test': config_test}
        conf_str = json.dumps(conf, indent=4)
        with open(configpath, 'w') as f:
            f.write(conf_str)

    @classmethod
    def get_conf(cls, conf_name):
        """和storage模块相关的配置"""
        with open(cls.configpath, 'r') as f:
            infos = f.read()
            infos = json.loads(infos)
            conf_ret = infos.get(conf_name, None)
            return conf_ret

    @classmethod
    def dump_conf(cls, conf_name, conf):
        """将配置存储"""
        with open(cls.configpath, 'r') as f:
            infos = f.read()
            infos = json.loads(infos)
        with open(cls.configpath, 'w') as f:
            infos[conf_name] = conf
            f.write(json.dumps(infos, indent=4))

class GuiManage:
    """管理token"""
    @staticmethod
    def get_token(ip, username, password):
        """登录并获取令牌"""

    @staticmethod
    def logout(token, ip):
        """退出登录以标记token失效"""


class GuiRequest:
    """发出请求并获取响应结果"""
    def __init__(self, token):
        """实例化时必须要有token才可以处理请求"""
        self.token = token
        self.headers = {'Authorization': f'Bearer {self.token}'}

    def handle_response(self, response:requests.Response, url, timeout):
        status_code = response.status_code
        content = response.content.decode()

        try:
            content = json.loads(content)
        except Exception as e:
            pass

        if status_code in [200, 201, 202]:
            return True, content
        else:
            return False, 'Error'
        
    def GET(self, url):
        response = requests.get(url, headers=self.headers)
        return self.handle_response(response, url, timeout=None) 
    
    def POST(self, url, data=None, timeout=60):
        if not data:
            data = {}
        response = requests.post(url, json=data, headers=self.headers)
        return self.handle_response(response, url, timeout=timeout)

    def DELETE(self, url, data=None, timeout=60):
        if not data:
            data = {}
        response = requests.delete(url, json=data, headers=self.headers)
        return self.handle_response(response, url, timeout=timeout)
    
    def PUT(self, url, data=None, timeout=60):
        if not data:
            data = {}
        response = requests.put(url, json=data, headers=self.headers)
        return self.handle_response(response, url, timeout=timeout)

