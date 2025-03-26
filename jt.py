import psutil
from scapy.all import *
import binascii
import json
import subprocess
from time import sleep
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
import cv2
import numpy as np
import pyautogui #这个后面打包了记得带上,是QQ输入信息和操作用的

current_dir = os.path.dirname(os.path.abspath(__file__))

config_path = os.getenv('CONFIG_PATH', 'config.json')
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

# 雷电模拟器adb配置
ADB_PATH = config["ADB_PATH"]
DEVICE_ID = config["DEVICE_ID"]

# 按钮坐标配置（720x1280分辨率）
BUTTONS = {
    '训练': (365, 945), #17正式开始育成
    '速': (60, 1040),
    '耐': (180, 1040),
    '力': (300, 1040),
    '根': (420, 1040),
    '智': (540, 1040),
    'SS': (660, 1040),
    '休息': (125, 945),
    '出行': (280, 1175),
    '比赛': (610, 1175),
    '参赛行程表': (610, 1080),
    '赛程表一': (610, 570),
    '赛程表二': (610, 790),
    '赛程表三': (610, 1000),
    '关闭': (360, 1210),
    '国外资质': (450, 1175),
    '友人':(350, 395),
    '担当':(350, 645),
    '确认参赛':(530, 890), #11确认萝卜氪体
    '远征_确认参赛':(530, 1180),
    '观看结果':(240, 1205),
    '继续':(470, 1205), #13确认开始培育
    '确认':(360, 1100),
    '远征_根':(250, 100),
    '远征_耐':(470, 100),
    '远征_力':(135, 250),
    '远征_速':(360, 250),
    '远征_智':(590, 250),
    '远征_技能点':(135, 380),
    '远征_体力':(360, 380),
    '远征_友情':(590, 380),
    '远征_金克斯':(250, 510),
    '远征_连霸':(470, 510),
    '远征_升级':(510, 720), #5选择借支援卡(6找到支援卡点击)
    '返回':(60, 1250),
    '选择一':(50, 830),
    '选择二':(50, 720),
    '选择三':(50, 610),
    '选择四':(50, 500),
    '选择五':(50, 390),
    '目标竞赛':(530, 840), #8确认回体
    '打开选单':(650, 1230), #14跳过剧本初动画
    '放弃':(550, 550),
    '确认放弃':(550, 860), #15确认跳过动画
    '逃':(600, 750),
    '先':(440, 750),
    '差':(280, 750),
    '追':(140, 750),
    '事件快进':(250, 1250), #16点两次
    '选择萝卜':(610, 180), #9
    '萝卜氪体':(530, 640), #10
    '确认育成':(450, 1075), #1育成，2选择剧本，3选择马娘，4选择种马，7开始育成，11.5确认体力已充，12开始培育
    '刷新好友卡':(650, 1000) #6.5
}

# 配置参数
TARGET_EXE = config["TARGET_EXE"]
FIXED_DST_PORT = 4693
support_card = config["support_card"]

# 全局变量
target_ports = set()
executor = ThreadPoolExecutor(max_workers=4)
packet_buffer = asyncio.Queue()
processing = True
current_round = 0
best_action = None
lock = threading.Lock()
screenshot = None
loop = None
isQieZhe = False
vitalshortage = 0
larc_zuoyueOutgoingRefused = False
larc_supportPtAll = 0
StatusSum = 400
minFriendship = 0
luck_value = 0
baseline = 31000
is_killed = False
found_card = False
unluck_times = 0
running = True

def adb_click(x, y, delay=0.55):
    rand_x = x + random.randint(-1, 1)
    rand_y = y + random.randint(-1, 1)
    rand_delay = delay + random.uniform(-0.05, 0.05)
    cmd = f'"{ADB_PATH}" -s {DEVICE_ID} shell input tap {rand_x} {rand_y}'
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"点击成功: ({rand_x}, {rand_y})，延迟: {rand_delay:.2f}s")
        else:
            print(f"点击失败: {result.stderr}")
    except Exception as e:
        print(f"命令执行异常: {str(e)}")
    sleep(rand_delay)

def perform_action(action_name):
    """执行完整的操作流程"""
    print(f"执行操作: {action_name}")
    
    actions = {
        "速训练": lambda: [adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['速']), adb_click(*BUTTONS['速']), sleep(0.5)],
        "耐训练": lambda: [adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['耐']), adb_click(*BUTTONS['耐']), sleep(0.5)],
        "力训练": lambda: [adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['力']), adb_click(*BUTTONS['力']), sleep(0.5)],
        "根训练": lambda: [adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['根']), adb_click(*BUTTONS['根']), sleep(0.5)],
        "智训练": lambda: [adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['智']), adb_click(*BUTTONS['智']), sleep(0.5)],
        "SS训练": lambda: [adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['SS']), adb_click(*BUTTONS['SS']), sleep(0.5)],
        "休息": lambda: [adb_click(*BUTTONS['休息']), sleep(0.5)],
        "友人出行": lambda: [adb_click(*BUTTONS['出行']), adb_click(*BUTTONS['友人']), sleep(0.5)],
        "单独出行": lambda: [adb_click(*BUTTONS['出行']), adb_click(*BUTTONS['担当']), sleep(0.5)],
        "比赛": lambda: [adb_click(*BUTTONS['比赛']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['确认参赛']), sleep(0.5)],
        "随机事件选择": lambda: [adb_click(*BUTTONS['选择二']), sleep(0.5)],
        "特殊事件选择": lambda: [adb_click(*BUTTONS['选择一']), sleep(0.5)],
        "出行事件选择": lambda: [adb_click(*BUTTONS['选择三']), sleep(0.5)],
        "目标选择一": lambda: [adb_click(*BUTTONS['选择五']), sleep(0.5)],
        "目标选择二": lambda: [adb_click(*BUTTONS['选择四']), sleep(0.5)],
        "继承": lambda: [adb_click(*BUTTONS['确认']), sleep(0.5)],
        "用闹钟": lambda: [adb_click(*BUTTONS['观看结果']), adb_click(*BUTTONS['继续']), sleep(0.5)],
        "赛前点适性": lambda: [adb_click(*BUTTONS['国外资质']), adb_click(*BUTTONS['远征_根']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_耐']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1)],
        "新人赛": lambda: [adb_click(*BUTTONS['确认']), sleep(1), adb_click(*BUTTONS['确认']), sleep(0.5), adb_click(*BUTTONS['确认参赛']), sleep(0.5)],
        "开始比赛": lambda: [adb_click(*BUTTONS['观看结果']), sleep(4), adb_click(*BUTTONS['返回']), sleep(2), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(0.5)],
        "比赛结束": lambda: [adb_click(*BUTTONS['继续']), sleep(2), adb_click(*BUTTONS['继续']), sleep(0.5)],
        "比赛结束补": lambda: [adb_click(*BUTTONS['继续'])],
        "凯旋门失败": lambda: [adb_click(*BUTTONS['观看结果']), adb_click(*BUTTONS['继续']), sleep(2), adb_click(*BUTTONS['继续']), sleep(0.5)],
        "目标达成": lambda: [adb_click(*BUTTONS['确认']), sleep(0.5)],
        "赛程赛": lambda: [adb_click(*BUTTONS['目标竞赛']), adb_click(*BUTTONS['目标竞赛']), sleep(1), adb_click(*BUTTONS['确认']), sleep(0.5), adb_click(*BUTTONS['确认参赛']), sleep(0.5)],
        "海外赛": lambda: [adb_click(*BUTTONS['确认']), sleep(1), adb_click(*BUTTONS['确认']), sleep(0.5), adb_click(*BUTTONS['远征_确认参赛']), sleep(0.5)],
        "确认补": lambda: [adb_click(*BUTTONS['确认']), sleep(0.5), adb_click(*BUTTONS['确认参赛'])],
        "海外确认参赛补": lambda: [adb_click(*BUTTONS['远征_确认参赛']), sleep(8), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回'])],
        "凯旋门": lambda: [adb_click(*BUTTONS['确认']), sleep(1), adb_click(*BUTTONS['确认']), sleep(0.5), adb_click(*BUTTONS['远征_确认参赛']), sleep(8), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回'])],
        "目标赛": lambda: [adb_click(*BUTTONS['确认']), sleep(1), adb_click(*BUTTONS['确认']), sleep(0.5), adb_click(*BUTTONS['确认参赛']), sleep(0.5)],
        "技能点适性": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_技能点']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1.5)],
        "远征速": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_速']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1.5), adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['速']), adb_click(*BUTTONS['速']), sleep(1)],
        "远征耐": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_耐']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1.5), adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['耐']), adb_click(*BUTTONS['耐']), sleep(1)],
        "远征力": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_力']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1.5), adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['力']), adb_click(*BUTTONS['力']), sleep(1)],
        "远征根": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_根']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1.5), adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['根']), adb_click(*BUTTONS['根']), sleep(1)],
        "远征智": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_智']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1.5), adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['智']), adb_click(*BUTTONS['智']), sleep(1)],
        "体速": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_体力']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1.5), adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['速']), adb_click(*BUTTONS['速']), sleep(1)],
        "体耐": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_体力']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1.5), adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['耐']), adb_click(*BUTTONS['耐']), sleep(1)],
        "体力": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_体力']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1.5), adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['力']), adb_click(*BUTTONS['力']), sleep(1)],
        "体根": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_体力']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1.5), adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['根']), adb_click(*BUTTONS['根']), sleep(1)],
        "体智": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_体力']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1.5), adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['智']), adb_click(*BUTTONS['智']), sleep(1)],
        "远征体速": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_速']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_体力']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1.5), adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['速']), adb_click(*BUTTONS['速']), sleep(1)],
        "远征体耐": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_耐']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_体力']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1.5), adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['耐']), adb_click(*BUTTONS['耐']), sleep(1)],
        "远征体力": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_力']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_体力']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1.5), adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['力']), adb_click(*BUTTONS['力']), sleep(1)],
        "远征体根": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_根']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_体力']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1.5), adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['根']), adb_click(*BUTTONS['根']), sleep(1)],
        "远征体智": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_智']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_体力']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1.5), adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['智']), adb_click(*BUTTONS['智']), sleep(1)],
        "远征训练补": lambda: [adb_click(*BUTTONS['返回']), sleep(0.5)],
        "友情适性": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_友情']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(0.5)],
        "跑法改逃": lambda: [adb_click(*BUTTONS['逃']), adb_click(*BUTTONS['逃']), adb_click(*BUTTONS['确认参赛']), sleep(0.5)],
        "跑法改先": lambda: [adb_click(*BUTTONS['逃']), adb_click(*BUTTONS['先']), adb_click(*BUTTONS['确认参赛']), sleep(0.5)],
        "跑法改差": lambda: [adb_click(*BUTTONS['逃']), adb_click(*BUTTONS['差']), adb_click(*BUTTONS['确认参赛']), sleep(0.5)],
        "跑法改追": lambda: [adb_click(*BUTTONS['逃']), adb_click(*BUTTONS['追']), adb_click(*BUTTONS['确认参赛']), sleep(0.5)],
        "放弃育成": lambda: [adb_click(*BUTTONS['打开选单']), adb_click(*BUTTONS['放弃']), adb_click(*BUTTONS['确认放弃'])],
        "确认育成": lambda: [adb_click(*BUTTONS['确认育成'])],
        "借卡": lambda: [adb_click(*BUTTONS['远征_升级'])],
        "刷新好友卡": lambda: [adb_click(*BUTTONS['刷新好友卡']), sleep(0.5)],
        "确认回体": lambda: [adb_click(*BUTTONS['目标竞赛']), sleep(0.5)],
        "选择萝卜": lambda: [adb_click(*BUTTONS['选择萝卜'])],
        "萝卜氪体": lambda: [adb_click(*BUTTONS['萝卜氪体']), sleep(0.5), adb_click(*BUTTONS['确认参赛'])],
        "确认培育": lambda: [adb_click(*BUTTONS['继续'])],
        "跳过剧本初动画": lambda: [adb_click(*BUTTONS['打开选单'])],
        "事件快进": lambda: [adb_click(*BUTTONS['事件快进']), adb_click(*BUTTONS['事件快进']), adb_click(*BUTTONS['训练'])],
        "借卡选择": lambda: [adb_click(*BUTTONS['远征_速'])],
    }
    
    if action := actions.get(action_name):
        action()
    else:
        print(f"未知的操作: {action_name}")

def parse_umaai_data(parameters):
    global current_round, best_action, luck_value, baseline, vitalshortage
    scores = {
        "回合数": float(parameters[1]),
        "预测分数": float(parameters[2]),
        "速训练": float(parameters[6]) + config["normal_scores"]["速训练"],
        "耐训练": float(parameters[7]) + config["normal_scores"]["耐训练"],
        "力训练": float(parameters[8]) + config["normal_scores"]["力训练"],
        "根训练": float(parameters[9]) + config["normal_scores"]["根训练"],
        "智训练": float(parameters[10]) + config["normal_scores"]["智训练"],
        "SS训练": float(parameters[11]) + config["normal_scores"]["SS训练"],
        "休息": float(parameters[12]) + config["normal_scores"]["休息"] - (200 if current_round in {0,1} else 0),
        "友人出行": float(parameters[13]) + config["normal_scores"]["友人出行"],
        "单独出行": float(parameters[14]) + config["normal_scores"]["单独出行"],
        "比赛": float(parameters[15]) + config["normal_scores"]["比赛"]
    }

    current_round = int(scores["回合数"])
    best_action = max(scores, key=scores.get)

    if best_action in {"速训练", "耐训练", "力训练", "根训练"}:
        vitalshortage += 20
    elif best_action in {"休息", "单独出行"}:
        vitalshortage -= 50
    elif best_action == "智训练":
        vitalshortage -= 5

    if current_round == 0:
        baseline = int(scores["预测分数"])
        print(f"当前回合: {current_round}, 预测分数: {baseline}, 建议操作: {best_action} (分数: {scores[best_action]})")
    else:
        luck_value = int(scores["预测分数"]) - baseline
        print(f"当前回合: {current_round}, 本局运气: {luck_value}, 建议操作: {best_action} (分数: {scores[best_action]})")
    return best_action

def parse_umaai_data_summer1(parameters):
    global current_round, best_action, luck_value
    scores = {
        "回合数": float(parameters[1]),
        "预测分数": float(parameters[2]),
        "速训练": float(parameters[6]) + config["summer1_scores"]["速训练"],
        "耐训练": float(parameters[7]) + config["summer1_scores"]["耐训练"],
        "力训练": float(parameters[8]) + config["summer1_scores"]["力训练"],
        "根训练": float(parameters[9]) + config["summer1_scores"]["根训练"],
        "智训练": float(parameters[10]) + config["summer1_scores"]["智训练"],
        "SS训练": float(parameters[11]) + config["summer1_scores"]["SS训练"],
        "休息": float(parameters[12]) + config["summer1_scores"]["休息"],
        "友人出行": float(parameters[13]) + config["summer1_scores"]["友人出行"],
        "单独出行": float(parameters[14]) + config["summer1_scores"]["单独出行"],
        "比赛": float(parameters[15]) + config["summer1_scores"]["比赛"],
        "远征速": float(parameters[16]) + config["summer1_scores"].get("远征速", 0),
        "远征耐": float(parameters[17]) + config["summer1_scores"].get("远征耐", 0),
        "远征力": float(parameters[18]) + config["summer1_scores"].get("远征力", 0),
        "远征根": float(parameters[19]) + config["summer1_scores"].get("远征根", 0),
        "远征智": float(parameters[20]) + config["summer1_scores"].get("远征智", 0),
    }

    current_round = int(scores["回合数"])
    best_action = max(scores, key=scores.get)
    luck_value = int(scores["预测分数"]) - baseline
    print(f"当前回合: {current_round}, 建议操作: {best_action} (分数: {scores[best_action]})")
    return best_action

def parse_umaai_data_summer2(parameters):
    global current_round, best_action
    scores = {
        "回合数": float(parameters[1]),
        "速训练": float(parameters[6]) + config["summer2_scores"]["速训练"],
        "耐训练": float(parameters[7]) + config["summer2_scores"]["耐训练"],
        "力训练": float(parameters[8]) + config["summer2_scores"]["力训练"],
        "根训练": float(parameters[9]) + config["summer2_scores"]["根训练"],
        "智训练": float(parameters[10]) + config["summer2_scores"]["智训练"],
        "SS训练": float(parameters[11]) + config["summer2_scores"]["SS训练"],
        "休息": float(parameters[12]) + config["summer2_scores"]["休息"],
        "友人出行": float(parameters[13]) + config["summer2_scores"]["友人出行"],
        "单独出行": float(parameters[14]) + config["summer2_scores"]["单独出行"],
        "比赛": float(parameters[15]) + config["summer2_scores"]["比赛"],
        "远征速": float(parameters[16]) + config["summer2_scores"].get("远征速", 0),
        "远征耐": float(parameters[17]) + config["summer2_scores"].get("远征耐", 0),
        "远征力": float(parameters[18]) + config["summer2_scores"].get("远征力", 0),
        "远征根": float(parameters[19]) + config["summer2_scores"].get("远征根", 0),
        "远征智": float(parameters[20]) + config["summer2_scores"].get("远征智", 0),
        "体速": float(parameters[26]) + config["summer2_scores"].get("体速", 0),
        "体耐": float(parameters[27]) + config["summer2_scores"].get("体耐", 0),
        "体力": float(parameters[28]) + config["summer2_scores"].get("体力", 0),
        "体根": float(parameters[29]) + config["summer2_scores"].get("体根", 0),
        "体智": float(parameters[30]) + config["summer2_scores"].get("体智", 0),
        "远征体速": float(parameters[36]) + config["summer2_scores"].get("远征体速", 0),
        "远征体耐": float(parameters[37]) + config["summer2_scores"].get("远征体耐", 0),
        "远征体力": float(parameters[38]) + config["summer2_scores"].get("远征体力", 0),
        "远征体根": float(parameters[39]) + config["summer2_scores"].get("远征体根", 0),
        "远征体智": float(parameters[40]) + config["summer2_scores"].get("远征体智", 0),
    }

    current_round = int(scores["回合数"])
    best_action = max(scores, key=scores.get)
    print(f"当前回合: {current_round}, 建议操作: {best_action} (分数: {scores[best_action]})")
    return best_action

def parse_server_data(data):
    """解析服务器发送的数据"""
    global isQieZhe, vitalshortage, larc_zuoyueOutgoingRefused, larc_supportPtAll, StatusSum, minFriendship
    try:
        json_data = json.loads(data)
        
        # 获取体力缺额
        vital = json_data.get('vital', 0)
        maxVital = json_data.get('maxVital', 0)
        vitalshortage = maxVital - vital

        # 是否切者
        isQieZhe = json_data.get('isQieZhe', False)
        
        # 总支持度
        larc_supportPtAll = json_data.get('larc_supportPtAll', 0)

        # 是否出行
        larc_zuoyueOutgoingRefused = json_data.get('larc_zuoyueOutgoingRefused', False)
        
        # 计算技能点和五维总和
        skillPt = json_data.get('skillPt', 0)
        five_status = json_data.get('fiveStatus', [])
        fiveStatusSum = sum(five_status) if five_status else 0
        StatusSum = fiveStatusSum + skillPt*config["skill_point_ratio"]/100
        
        # 获取非-1的cardIdInGame对应的friendship
        persons = json_data.get('persons', [])
        valid_friendships = [p.get('friendship', 0) for p in persons 
                           if p.get('cardIdInGame', -1) != -1]
        
        # 获取最低的友情值
        minFriendship = min(valid_friendships) if valid_friendships else 0
        
        print(f"""
            状态信息:
            体力: {vital}/{maxVital}
            总支持度: {larc_supportPtAll}
            五维总和: {fiveStatusSum}
            技能点: {skillPt}
            最低友情度: {minFriendship}
        """)
        
        return isQieZhe
        
    except json.JSONDecodeError:
        print("JSON解析失败")
        return None
    except Exception as e:
        print(f"解析服务器数据异常: {str(e)}")
        return None

def get_target_ports_once():
    """启动时一次性获取目标端口"""
    global target_ports
    for conn in psutil.net_connections(kind='tcp'):
        if conn.status == 'ESTABLISHED' and conn.pid:
            try:
                process = psutil.Process(conn.pid)
                if process.exe() == TARGET_EXE:
                    target_ports.add(conn.laddr.port)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    print("爱脚本启动成功，如有问题请找作者QQ2269430789(小力)")
    print(f"初始目标端口: {target_ports}")

def websocket_decrypt(raw_data):
    """解密函数"""
    try:
        # 快速检查数据有效性
        if len(raw_data) < 16:  # 至少需要8字节
            return None
            
        # 直接处理二进制数据，跳过hex转换
        mask_key = raw_data[4:8]
        masked_payload = raw_data[8:]
        
        # 使用列表推导式优化解密过程
        decrypted = bytes(b ^ mask_key[i % 4] for i, b in enumerate(masked_payload))
        return decrypted.decode('utf-8', 'ignore')
    except Exception as e:
        print(f"解密异常: {str(e)}")
        return None
    
def websocket_decode(raw_data):
    """解码WebSocket数据帧"""
    try:
        if len(raw_data) < 2:
            return None
            
        # 获取第二个字节（包含payload长度信息）
        second_byte = raw_data[1]
        payload_length = second_byte & 127
        mask_offset = 2
        
        # 处理扩展长度
        if payload_length == 126:
            payload_length = int.from_bytes(raw_data[2:4], 'big')
            mask_offset = 4
        elif payload_length == 127:
            payload_length = int.from_bytes(raw_data[2:10], 'big')
            mask_offset = 10
            
        # 检查是否有掩码
        is_masked = (second_byte & 0x80) != 0
        
        if is_masked:
            # 获取掩码密钥
            mask_key = raw_data[mask_offset:mask_offset + 4]
            payload_offset = mask_offset + 4
            
            # 解码payload
            payload = bytes(b ^ mask_key[i % 4] for i, b in enumerate(raw_data[payload_offset:]))
        else:
            # 未掩码的payload
            payload = raw_data[mask_offset:]
            
        return payload.decode('utf-8')
    except Exception as e:
        print(f"WebSocket解码异常: {str(e)}")
        return None

async def process_packet_queue():
    """异步处理数据包队列"""
    while processing:
        try:
            source, packet_data = await packet_buffer.get()
            
            if source == "client":
                if "PrintUmaAiResult" in packet_data:
                    # 处理客户端数据
                    data = json.loads(packet_data)
                    params = data["Parameters"][0].split()
                    params = [float(p) if not p.startswith('-') and p.replace('.', '', 1).isdigit() else 0.0 
                             for p in params]
                    
                    if current_round >= 58 and len(params) >= 30:
                        parse_umaai_data_summer2(params)
                    elif current_round >= 35 and current_round <= 41 and len(params) >= 25:
                        parse_umaai_data_summer1(params)
                    elif len(params) >= 14:
                        parse_umaai_data(params)
            elif source == "server":
                parse_server_data(packet_data)
            
            packet_buffer.task_done()
        except Exception as e:
            print(f"处理包异常: {str(e)}")

def init_async():
    """初始化异步相关内容"""
    global loop, packet_buffer
    
    # 创建新的事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # 创建异步队列
    packet_buffer = asyncio.Queue()
    
    # 启动异步处理队列
    loop.create_task(process_packet_queue())
    
    # 在新线程中启动事件循环
    thread = threading.Thread(target=run_event_loop, daemon=True)
    thread.start()
    
    return thread

def run_event_loop():
    """在线程中运行事件循环"""
    global loop
    try:
        loop.run_forever()
    except Exception as e:
        print(f"事件循环异常: {str(e)}")
    finally:
        loop.close()

def packet_callback(packet):
    """数据包回调函数"""
    global loop
    try:
        if not packet.haslayer(TCP):
            return
            
        # 检查是否为客户端到服务器的通信
        if packet[TCP].dport == FIXED_DST_PORT and packet[TCP].sport in target_ports:
            if not packet.haslayer(Raw):
                return
                
            payload = bytes(packet[Raw])
            if len(payload) < 60:
                return
                
            if result := websocket_decrypt(payload):
                if loop and not loop.is_closed():
                    future = asyncio.run_coroutine_threadsafe(packet_buffer.put(("client", result)), loop)
                    future.result()
        
        # 检查是否为服务器到客户端的通信
        elif packet[TCP].sport == FIXED_DST_PORT and packet[TCP].dport in target_ports:
            if not packet.haslayer(Raw):
                return
                
            payload = bytes(packet[Raw])
            if len(payload) >= 1000:
                if decoded_data := websocket_decode(payload):
                    if loop and not loop.is_closed():
                        future = asyncio.run_coroutine_threadsafe(packet_buffer.put(("server", decoded_data)), loop)
                        future.result()
            
    except Exception as e:
        print(f"回调异常: {str(e)}")

def start_capture():
    """抓包函数"""
    print("启动高速流量监控...")
    
    # 设置BPF过滤器，包含双向流量
    filter_str = f"tcp and ("
    filter_str += f"(dst port {FIXED_DST_PORT} and ("
    filter_str += " or ".join(f"src port {port}" for port in target_ports)
    filter_str += f")) or (src port {FIXED_DST_PORT} and ("
    filter_str += " or ".join(f"dst port {port}" for port in target_ports)
    filter_str += ")))"
    
    print(f"使用过滤器: {filter_str}")  # 打印过滤器以便调试
    
    # 使用AsyncSniffer进行异步抓包
    sniffer = AsyncSniffer(
        iface=r'\Device\NPF_Loopback',
        filter=filter_str,
        prn=packet_callback,
        store=0  # 不保存包，减少内存使用
    )
    
    return sniffer

def capture_screenshot():
    """使用ADB截图并返回截图数据"""
    try:
        cmd = [
            ADB_PATH,
            '-s', DEVICE_ID,
            'exec-out', 'screencap', '-p'
        ]
        
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        nparr = np.frombuffer(result.stdout, np.uint8)
        screenshot = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        print(f"正在检测状态")
        return screenshot
    
    except subprocess.CalledProcessError as e:
        print(f"截图失败：{e.stderr.decode('utf-8')}")
        return None
    except Exception as e:
        print(f"发生未知错误：{str(e)}")
        return None

def check_game_state():
    """检查游戏状态"""
    global best_action, screenshot, is_killed, current_round, isQieZhe, found_card, unluck_times, luck_value
    while True:
        with lock:
            screenshot = capture_screenshot()

        if screenshot is None:
            sleep(1)
            continue
        
        # 预加载所有图片
        images = {
            'lace_lose_img': cv2.imread(os.path.join(current_dir, 'picture/0.png')),
            'event_choice_img': cv2.imread(os.path.join(current_dir, 'picture/1.png')),
            'event_choice1_img': cv2.imread(os.path.join(current_dir, 'picture/13.png')),
            'five_choice_one_img': cv2.imread(os.path.join(current_dir, 'picture/2.png')),
            'greenhat_ask_img': cv2.imread(os.path.join(current_dir, 'picture/3.png')),
            '1_img': cv2.imread(os.path.join(current_dir, 'picture/4.png')),
            'object_lace_img': cv2.imread(os.path.join(current_dir, 'picture/5.png')),
            'communicate_lace_img': cv2.imread(os.path.join(current_dir, 'picture/6.png')),
            'training_img': cv2.imread(os.path.join(current_dir, 'picture/7.png')),
            'kaigai_training_img': cv2.imread(os.path.join(current_dir, 'picture/8.png')),
            'beats_img': cv2.imread(os.path.join(current_dir, 'picture/9.png')),
            'trip_img': cv2.imread(os.path.join(current_dir, 'picture/10.png')),
            'none_img': cv2.imread(os.path.join(current_dir, 'picture/11.png')),
            'continue_img': cv2.imread(os.path.join(current_dir, 'picture/12.png')),
            'before_lace_img': cv2.imread(os.path.join(current_dir, 'picture/14.png')),
            'clock_img': cv2.imread(os.path.join(current_dir, 'picture/15.png')),
            'lace_over1_img': cv2.imread(os.path.join(current_dir, 'picture/16.png')),
            'lace_over2_img': cv2.imread(os.path.join(current_dir, 'picture/17.png')),
            'lace_over3_img': cv2.imread(os.path.join(current_dir, 'picture/18.png')),
            'lace_over4_img': cv2.imread(os.path.join(current_dir, 'picture/19.png')),
            'add_training_img': cv2.imread(os.path.join(current_dir, 'picture/20.png')),
            'lace_confirm_img': cv2.imread(os.path.join(current_dir, 'picture/21.png')),
            'lace_kaigai_confirm_img': cv2.imread(os.path.join(current_dir, 'picture/22.png')),
            'continue_action_img': cv2.imread(os.path.join(current_dir, 'picture/23.png')),
            'main_interface_img': cv2.imread(os.path.join(current_dir, 'picture/24.png')),
            'friend_supportcard_into_img': cv2.imread(os.path.join(current_dir, 'picture/25.png')),
            'friend_supportcard_interface_img': cv2.imread(os.path.join(current_dir, 'picture/26.png')),
            'vital_add_into_img': cv2.imread(os.path.join(current_dir, 'picture/27.png')),
            'vital_add_interface_img': cv2.imread(os.path.join(current_dir, 'picture/28.png')),
            'begin_into_img': cv2.imread(os.path.join(current_dir, 'picture/29.png')),
            'goto_begin_img': cv2.imread(os.path.join(current_dir, 'picture/30.png')),
            'timeout_img': cv2.imread(os.path.join(current_dir, 'picture/33.png')),
            '03120_img': cv2.imread(os.path.join(current_dir, 'picture/03120.png')),
            '03820_img': cv2.imread(os.path.join(current_dir, 'picture/03820.png')),
            '06510_img': cv2.imread(os.path.join(current_dir, 'picture/06510.png')),
            '201_img': cv2.imread(os.path.join(current_dir, 'picture/201.png')),
            '202_img': cv2.imread(os.path.join(current_dir, 'picture/202.png')),
            '203_img': cv2.imread(os.path.join(current_dir, 'picture/203.png')),
            '204_img': cv2.imread(os.path.join(current_dir, 'picture/204.png')),
            '205_img': cv2.imread(os.path.join(current_dir, 'picture/205.png')),
            '206_img': cv2.imread(os.path.join(current_dir, 'picture/206.png')),
            '207_img': cv2.imread(os.path.join(current_dir, 'picture/207.png')),
            '208_img': cv2.imread(os.path.join(current_dir, 'picture/208.png')),
            '209_img': cv2.imread(os.path.join(current_dir, 'picture/209.png')),
            '210_img': cv2.imread(os.path.join(current_dir, 'picture/210.png')),
        }

        # 定义所有ROI
        rois = {
            'lace_lose_roi': screenshot[1136:1226, 63:353],
            'event_choice_roi': screenshot[81:130, 615:700],
            'five_choice_one_roi': screenshot[198:328, 0:600],
            'greenhat_ask_roi': screenshot[200:287, 0:720],
            '1_roi': screenshot[388:588, 9:709],
            'object_lace_roi': screenshot[1030:1130, 74:169],
            'communicate_lace_roi': screenshot[1046:1123, 524:671],
            'training_roi': screenshot[938:1044, 70:170],
            'kaigai_training_roi': screenshot[937:1045, 70:165],
            'beats_roi': screenshot[1025:1077, 266:451],
            'trip_roi': screenshot[199:449, 1:711],
            'none_roi': screenshot[1195:1271, 522:580],
            'continue_roi': screenshot[1085:1137, 219:502],
            'before_lace_roi': screenshot[1140:1213, 175:335],
            'clock_roi': screenshot[1120:1280, 0:720],
            'lace_over1_roi': screenshot[1130:1280, 360:720],
            'lace_over2_roi': screenshot[1205:1280, 0:720],
            'lace_over3_roi': screenshot[699:899, 0:720],
            'add_training_roi': screenshot[235:285, 110:552],
            'lace_confirm_roi': screenshot[1038:1138, 1:511],
            'lace_kaigai_confirm_roi': screenshot[1130:1230, 0:720],
            'continue_action_roi': screenshot[1180:1280, 0:720],
            'main_interface_roi': screenshot[1223:1266, 455:692],
            'friend_supportcard_into_roi': screenshot[535:795, 494:649],
            'friend_supportcard_interface_roi': screenshot[35:90, 9:709],
            'vital_add_into_roi': screenshot[739:889, 10:710],
            'vital_add_interface1_roi': screenshot[35:90, 8:708],
            'vital_add_interface2_roi': screenshot[299:354, 8:708],
            'vital_add_interface3_roi': screenshot[383:438, 8:708],
            'begin_into_roi': screenshot[1120:1280, 0:720],
            'goto_begin_roi': screenshot[870:1280, 0:640],
            'timeout_roi': screenshot[390:890, 10:710],
            'follow_friend_roi': screenshot[210:385, 479:684],
            'follow_friend1_roi': screenshot[212:387, 479:684],
            'friend_supportcard_roi': screenshot[229:364, 37:139],
            'supportcard_event_roi': screenshot[195:285, 0:720]
        }
        
        if screenshot is not None:
            if running == False:
                print("脚本暂停中")
                sleep(1)
            elif isQieZhe == True:
                print("检测到天赋异禀，鼠标给你你来玩")
                send_qq_message()
                result = waitting_for_play()
                if result == "育成结束，下一把":
                    current_round = 0
                    is_killed = True
                    isQieZhe = False
                else:
                    input("\n按任意键继续...")
            elif match_template(rois['timeout_roi'], images['timeout_img']):
                print("网络连接超时")
                perform_action("确认回体")
            elif is_killed == True:
                if match_template(rois['main_interface_roi'], images['main_interface_img']):
                    if match_template(rois['friend_supportcard_into_roi'], images['friend_supportcard_into_img']):
                        perform_action("借卡")
                    else:
                        perform_action("确认育成")
                elif match_template(rois['friend_supportcard_interface_roi'], images['friend_supportcard_interface_img']):
                    page_count = 0
                    max_pages = 20
                    while page_count < max_pages and not found_card:
                        result = find_and_click_support_card()
                        if result == "找到卡":
                            sleep(1)
                            found_card = True
                            break
                        elif result == "需要滑动":
                            sleep(4)
                            continue
                        elif result == "需要刷新":
                            print(f"本页未找到，刷新{page_count}次")
                            perform_action("刷新好友卡")
                            page_count += 1
                            sleep(4)
                            continue
                        elif result == "截图失败":
                            sleep(1)
                            continue
                    if not found_card:
                        print(f"已检查 {max_pages} 次，未找到目标支援卡，请追随一个携带所需支援卡的玩家")
                    sleep(1)
                elif match_template(rois['vital_add_into_roi'], images['vital_add_into_img']):
                    perform_action("确认回体")
                elif match_template(rois['vital_add_interface1_roi'], images['vital_add_interface_img']):
                    perform_action("选择萝卜")
                elif match_template(rois['vital_add_interface2_roi'], images['vital_add_interface_img']):
                    perform_action("萝卜氪体")
                elif match_template(rois['vital_add_interface3_roi'], images['vital_add_interface_img']):
                    perform_action("确认育成")
                elif match_template(rois['begin_into_roi'], images['begin_into_img']):
                    perform_action("确认培育")
                elif match_template(rois['goto_begin_roi'], images['goto_begin_img']):
                    sleep(1)
                    perform_action("事件快进")
                    is_killed = False
                    found_card = False
                    current_round = 0
                else:
                    sleep(3)
                    screenshot = capture_screenshot()
                    rois['main_interface_roi'] = screenshot[1223:1266, 455:692]
                    if not match_template(rois['main_interface_roi'], images['main_interface_img']) and found_card == True:
                        perform_action("跳过剧本初动画")
            elif larc_zuoyueOutgoingRefused == True:
                print("检测到赌黄帽失败")
                perform_action("放弃育成")
                is_killed = True
            elif current_round == 22 and match_template(rois['training_roi'], images['training_img']) and best_action is not None:
                perform_action("赛前点适性")
                screenshot = capture_screenshot()
                rois['continue_action_roi'] = screenshot[1180:1280, 0:720]
                if match_template(rois['continue_action_roi'], images['continue_action_img']):
                    perform_action("远征训练补")
                executor.submit(perform_action, best_action)
                best_action = None
            elif current_round == 41 and match_template(rois['kaigai_training_roi'], images['kaigai_training_img']) and best_action is not None:
                input("\n临时暂停键按任意键继续...记得关掉脚本")
                perform_action("友情适性")
                sleep(2)
                executor.submit(perform_action, best_action)
                best_action = None
            elif current_round == 41 and match_template(rois['object_lace_roi'], images['object_lace_img']):
                    print("检测到初次凯旋门")
                    input("\n按任意键继续...")
                    #perform_action("初次凯旋门适性检查")
                    perform_action("海外赛")
            elif current_round == 65 and match_template(rois['object_lace_roi'], images['object_lace_img']):
                    print("检测到最终凯旋门")
                    input("\n按任意键继续...")
                    #perform_action("凯旋门适性检查")
                    perform_action("凯旋门")
            elif (match_template(rois['event_choice_roi'], images['event_choice_img']) and match_template(rois['none_roi'], images['none_img'])) or (match_template(rois['event_choice_roi'], images['event_choice1_img']) and match_template(rois['none_roi'], images['none_img'])):
                sleep(2.7)
                screenshot = capture_screenshot()
                rois['five_choice_one_roi'] = screenshot[198:328, 0:600]  # 更新ROI
                rois['greenhat_ask_roi'] = screenshot[200:287, 0:720]
                rois['trip_roi'] = screenshot[199:449, 1:711]
                rois['event_choice_roi'] = screenshot[81:130, 615:700]
                rois['none_roi'] = screenshot[1195:1271, 522:580]
                rois['add_training_roi'] = screenshot[235:285, 110:552]
                rois['supportcard_event_roi'] = screenshot[195:285, 0:720]
                if match_template(rois['five_choice_one_roi'], images['five_choice_one_img']):
                    print("检测到五选一")
                    if config["five_choice_one_action"] == "目标选择二":
                        perform_action("目标选择二")
                    elif config["five_choice_one_action"] == "目标选择三":
                        perform_action("出行事件选择")
                    elif config["five_choice_one_action"] == "目标选择四":
                        perform_action("随机事件选择")
                    elif config["five_choice_one_action"] == "目标选择五":
                        perform_action("特殊事件选择")
                    else:
                        perform_action("目标选择一")
                elif match_template(rois['supportcard_event_roi'], images['207_img']):
                    print("检测到芝麻给回避")
                    perform_action("出行事件选择")
                elif match_template(rois['trip_roi'], images['trip_img']):
                    print("检测到出行事件")
                    if vitalshortage >= config["min_vital_for_yellow_hat"]:
                        print("赌黄帽")
                        perform_action("随机事件选择")
                    else:
                        print("不赌黄帽")
                        perform_action("出行事件选择")
                elif match_template(rois['greenhat_ask_roi'], images['greenhat_ask_img']) or match_template(rois['add_training_roi'], images['add_training_img']) or match_template(rois['supportcard_event_roi'], images['03120_img']) or match_template(rois['supportcard_event_roi'], images['03820_img']) or match_template(rois['supportcard_event_roi'], images['06510_img']) or match_template(rois['supportcard_event_roi'], images['202_img']) or match_template(rois['supportcard_event_roi'], images['209_img']) or (vitalshortage >= config["vital_add_choice"]["vital10"] and match_template(rois['supportcard_event_roi'], images['203_img'])) or (vitalshortage >= config["vital_add_choice"]["vital10"] and match_template(rois['supportcard_event_roi'], images['205_img'])) or (vitalshortage >= config["vital_add_choice"]["vital10"] and match_template(rois['supportcard_event_roi'], images['206_img'])) or (vitalshortage >= config["vital_add_choice"]["vital10"] and match_template(rois['supportcard_event_roi'], images['210_img'])) or (vitalshortage >= config["vital_add_choice"]["vital15"] and match_template(rois['supportcard_event_roi'], images['201_img'])) or (vitalshortage >= config["vital_add_choice"]["vital2025"] and match_template(rois['supportcard_event_roi'], images['204_img'])) or (vitalshortage >= config["vital_add_choice"]["vital2025"] and match_template(rois['supportcard_event_roi'], images['208_img'])):
                    print("检测到特殊事件")
                    perform_action("特殊事件选择")
                elif (match_template(rois['event_choice_roi'], images['event_choice_img']) and match_template(rois['none_roi'], images['none_img'])) or (match_template(rois['event_choice_roi'], images['event_choice1_img']) and match_template(rois['none_roi'], images['none_img'])):
                    print("检测到事件选择")
                    perform_action("随机事件选择")
            elif match_template(rois['training_roi'], images['training_img']) and best_action is not None:
                if current_round == 30:
                    print("开启第三过滤器")
                    if minFriendship < config["filters"]["继承"]["minFriendship"] or StatusSum < config["filters"]["继承"]["minStatusSum"] or larc_supportPtAll < config["filters"]["继承"]["minlarc_supportPtAll"]:
                        print(f"最低羁绊: {minFriendship}/{config['filters']['继承']['minFriendship']}, 总属性: {StatusSum}/{config['filters']['继承']['minStatusSum']}, 总支持度: {larc_supportPtAll}/{config['filters']['继承']['minlarc_supportPtAll']}")
                        print("不通过，放弃育成")
                        perform_action("放弃育成")
                        is_killed = True
                    else:
                        print("通过，继续育成")
                        if config["filters"]["继承"]["pause_after_pass"] == True:
                            send_qq_message()
                            result = waitting_for_play()
                            if result == "育成结束，下一把":
                                current_round = 0
                                is_killed = True
                                isQieZhe = False
                            else:
                                input("\n按任意键继续...")
                sleep(1.2)
                screenshot = capture_screenshot()
                rois['training_roi'] = screenshot[938:1044, 70:170]
                if match_template(rois['training_roi'], images['training_img']) and best_action is not None:
                    if (current_round in {1, 2, 3, 4} and luck_value <= config["luck_thresholds"]["early"]) or (current_round in {5, 6, 7, 8, 9, 10} and luck_value <= config["luck_thresholds"]["mid"]) or (current_round >= 11 and current_round <= 23 and luck_value <= config["luck_thresholds"]["late"]) or (current_round >= 25 and luck_value <= 400):
                        print("检测到本局运气低于标准")
                        if unluck_times == 2:
                            print(f"已经忍{unluck_times}次, 当前回合: {current_round}, 本局运气: {luck_value} ")
                            perform_action("放弃育成")
                            is_killed = True
                        else:
                            unluck_times += 1
                            print(f"忍{unluck_times}次")
                            executor.submit(perform_action, best_action)
                            best_action = None
                    else:
                        unluck_times = 0
                        print("检测到训练界面")
                        executor.submit(perform_action, best_action)
                        best_action = None
            elif match_template(rois['kaigai_training_roi'], images['kaigai_training_img']) and best_action is not None:
                print("检测到远征训练界面")
                if current_round == 36:
                    perform_action("技能点适性")
                if luck_value >= 500:
                    unluck_times = 0
                    executor.submit(perform_action, best_action)
                else:
                    print("检测到本局运气低于标准")
                    if unluck_times == 2:
                        print(f"当前回合: {current_round}, 本局运气: {luck_value} ")
                        perform_action("放弃育成")
                        is_killed = True
                    else:
                        unluck_times += 1
                        print(f"忍{unluck_times}次")
                        executor.submit(perform_action, best_action)
                screenshot = capture_screenshot()
                rois['continue_action_roi'] = screenshot[1180:1280, 0:720]
                if match_template(rois['continue_action_roi'], images['continue_action_img']):
                    perform_action("远征训练补")
                    continue_action = best_action[-1] + "训练"
                    executor.submit(perform_action, continue_action)
                best_action = None
            elif match_template(rois['beats_roi'], images['beats_img']):
                print("检测到继承")
                perform_action("继承")
            elif match_template(rois['communicate_lace_roi'], images['communicate_lace_img']):
                print("检测到交流战")
                if current_round == 23:
                    print("开启第二过滤器")
                    if minFriendship < config["filters"]["第一次交流战前"]["minFriendship"] or StatusSum < config["filters"]["第一次交流战前"]["minStatusSum"] or larc_supportPtAll < config["filters"]["第一次交流战前"]["minlarc_supportPtAll"]:
                        print(f"最低羁绊: {minFriendship}/{config['filters']['第一次交流战前']['minFriendship']}, 总属性: {StatusSum}/{config['filters']['第一次交流战前']['minStatusSum']}, 总支持度: {larc_supportPtAll}/{config['filters']['第一次交流战前']['minlarc_supportPtAll']}")
                        print("不通过，放弃育成")
                        perform_action("放弃育成")
                        is_killed = True
                    else:
                        print("通过，继续育成")
                        if config["filters"]["第一次交流战前"]["pause_after_pass"] == True:
                            send_qq_message()
                            result = waitting_for_play()
                            if result == "育成结束，下一把":
                                current_round = 0
                                isQieZhe = False
                            else:
                                input("\n按任意键继续...")
                        else:
                            perform_action("海外赛")
                elif current_round == 35:
                    print("开启第四过滤器")
                    if minFriendship < config["filters"]["第二次交流战前"]["minFriendship"] or StatusSum < config["filters"]["第二次交流战前"]["minStatusSum"] or larc_supportPtAll < config["filters"]["第二次交流战前"]["minlarc_supportPtAll"]:
                        print(f"最低羁绊: {minFriendship}/{config['filters']['第二次交流战前']['minFriendship']}, 总属性: {StatusSum}/{config['filters']['第二次交流战前']['minStatusSum']}, 总支持度: {larc_supportPtAll}/{config['filters']['第二次交流战前']['minlarc_supportPtAll']}")
                        print("不通过，放弃育成")
                        perform_action("放弃育成")
                        is_killed = True
                    else:
                        print("通过，继续育成")
                        if config["filters"]["第二次交流战前"]["pause_after_pass"] == True:
                            send_qq_message()
                            result = waitting_for_play()
                            if result == "育成结束，下一把":
                                current_round = 0
                                isQieZhe = False
                            else:
                                input("\n按任意键继续...")
                        else:
                            perform_action("海外赛")
                else:
                    perform_action("海外赛")
            elif match_template(rois['object_lace_roi'], images['object_lace_img']):
                if current_round == 10:
                    print("检测到出道战")
                    print("开启第一过滤器")
                    if minFriendship < config["filters"]["出道"]["minFriendship"] or StatusSum < config["filters"]["出道"]["minStatusSum"] or larc_supportPtAll < config["filters"]["出道"]["minlarc_supportPtAll"]:
                        print(f"最低羁绊: {minFriendship}/{config['filters']['出道']['minFriendship']}, 总属性: {StatusSum}/{config['filters']['出道']['minStatusSum']}, 总支持度: {larc_supportPtAll}/{config['filters']['出道']['minlarc_supportPtAll']}")
                        print("不通过，放弃育成")
                        perform_action("放弃育成")
                        is_killed = True
                    else:
                        print("通过，继续育成")
                        if config["filters"]["出道"]["pause_after_pass"] == True:
                            send_qq_message()
                            result = waitting_for_play()
                            if result == "育成结束，下一把":
                                current_round = 0
                                isQieZhe = False
                            else:
                                input("\n按任意键继续...")
                        else:
                            perform_action("新人赛")
                elif current_round in {32, 58}:
                    print("检测到目标赛")
                    perform_action("目标赛")
                elif current_round in {39, 63}:
                    print("检测到海外赛")
                    perform_action("海外赛")
                elif current_round in {41, 65}:
                    print("检测到凯旋门，请自行选择远征适性和技能后进入参赛界面再继续脚本")
                    input("\n按任意键继续...")
            elif match_template(rois['before_lace_roi'], images['before_lace_img']):
                if current_round in config["run_styles"].get("逃", []):
                    print("更改跑法逃")
                    perform_action("跑法改逃")
                elif current_round in config["run_styles"].get("先", []):
                    print("更改跑法先")
                    perform_action("跑法改先")
                elif current_round in config["run_styles"].get("差", []):
                    print("更改跑法差")
                    perform_action("跑法改差")
                elif current_round in config["run_styles"].get("追", []):
                    print("更改跑法追")
                    perform_action("跑法改追")
                print("开始比赛")
                perform_action("开始比赛")
            elif match_template(rois['continue_roi'], images['continue_img']):
                print("检测到目标达成")
                perform_action("目标达成")
            elif match_template(rois['lace_lose_roi'], images['lace_lose_img']) and config["use_alarm"] == "是":
                print("检测到比赛失败，闹钟启动")
                perform_action("用闹钟")
            elif match_template(rois['lace_confirm_roi'], images['lace_confirm_img']):
                print("检测到漏点确认")
                perform_action("确认补")
            elif match_template(rois['lace_kaigai_confirm_roi'], images['lace_kaigai_confirm_img']):
                print("检测到漏点海外确认参赛")
                perform_action("海外确认参赛补")
            elif match_template(rois['lace_over3_roi'], images['lace_over3_img']) or match_template(rois['lace_over2_roi'], images['lace_over2_img']) or match_template(rois['lace_over2_roi'], images['lace_over4_img']):
                print("检测到比赛结束")
                perform_action("比赛结束补")
            elif match_template(rois['lace_over1_roi'], images['lace_over1_img']):
                print("检测到比赛结束")
                perform_action("比赛结束")
            
        sleep(1)

def match_template(roi, template):
    """模板匹配"""
    res = cv2.matchTemplate(roi, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.99
    loc = np.where(res >= threshold)
    return len(loc[0]) > 0

def find_and_click_support_card():
    """在整个列表区域查找支援卡并点击第一个匹配项，
    如果未找到则检查follow_friend区域并执行相应操作"""
    images = {
        'follow_friend_img': cv2.imread(os.path.join(current_dir, 'picture/31.png')),
        'follow_friend1_img': cv2.imread(os.path.join(current_dir, 'picture/32.png')),
        '101_img': cv2.imread(os.path.join(current_dir, 'picture/101.png')),
        '102_img': cv2.imread(os.path.join(current_dir, 'picture/102.png')),
        '103_img': cv2.imread(os.path.join(current_dir, 'picture/103.png')),
        '104_img': cv2.imread(os.path.join(current_dir, 'picture/104.png'))
    }
    screenshot = capture_screenshot()
    if screenshot is None:
        print("截图失败")
        return "截图失败"
    
    # 1. 首先尝试查找支援卡
    # 扩展检测区域到整个可能包含支援卡的区域
    extended_roi = screenshot[110:970, 37:139]
    
    template = images[support_card]
    result = cv2.matchTemplate(extended_roi, template, cv2.TM_CCOEFF_NORMED)
    
    threshold = 0.96
    locations = np.where(result >= threshold)
    match_points = list(zip(*locations[::-1]))
    
    if match_points:
        # 找到支援卡，按y坐标排序，获取最上面的一个
        match_points.sort(key=lambda p: p[1])
        x, y = match_points[0]
        
        # 计算模板中心点在原始图像中的坐标
        h, w = template.shape[:2]
        center_x = x + w // 2 + 37  # 加上ROI的x偏移
        center_y = y + h // 2 + 100  # 加上ROI的y偏移
        
        print(f"找到目标支援卡，位置: ({center_x}, {center_y})")
        
        # 点击找到的支援卡
        adb_click(center_x, center_y)
        return "找到卡"
    
    # 2. 如果没找到支援卡，检查是否可以滑动
    extended2_roi = screenshot[110:970, 479:684]
    
    template1 = images['follow_friend_img']
    result1 = cv2.matchTemplate(extended2_roi, template1, cv2.TM_CCOEFF_NORMED)
    locations1 = np.where(result1 >= threshold)
    match_points1 = list(zip(*locations1[::-1]))
    
    if match_points1:
        subprocess.run(f'"{ADB_PATH}" -s {DEVICE_ID} shell input swipe 360 800 360 350 600', shell=True, capture_output=True, text=True, timeout=15)
        print("执行滑动操作")
        return "需要滑动"
    
    template2 = images['follow_friend1_img']
    result2 = cv2.matchTemplate(extended2_roi, template2, cv2.TM_CCOEFF_NORMED)
    locations2 = np.where(result2 >= threshold)
    match_points2 = list(zip(*locations2[::-1]))
    
    if match_points2:
        subprocess.run(f'"{ADB_PATH}" -s {DEVICE_ID} shell input swipe 360 800 360 350 900', 
                      shell=True, capture_output=True, text=True, timeout=5)
        print("执行滑动操作")
        return "需要滑动"
    
    # 3. 如果既没找到支援卡也没找到可滑动区域，则刷新页面
    return "需要刷新"

def send_qq_message():
    try:
        # 确保QQ窗口已打开且处于焦点状态
        # 模拟键盘输入（支持中文需切换输入法）
        pyautogui.click(500, 1140)
        sleep(0.3)
        pyautogui.write("1111")
        sleep(0.3)
        pyautogui.press("enter")
        print("QQ消息已发送")
    except Exception as e:
        print(f"消息发送失败: {str(e)}")

def waitting_for_play():
    send_order = False
    images = {
        '0_0_img': cv2.imread(os.path.join(current_dir, 'picture/0_0.png'))
    }

    while not send_order:
        try:
            # 使用pyautogui截图并转换为OpenCV格式
            screenshot_pil = pyautogui.screenshot()
            screenshot_cv = cv2.cvtColor(np.array(screenshot_pil), cv2.COLOR_RGB2BGR)
            if screenshot_cv is None:
                print("截图失败")
                return "截图失败"
    
            extended_roi = screenshot_cv[975:1025, 1115:1185]
    
            template = images['0_0_img']
            result = cv2.matchTemplate(extended_roi, template, cv2.TM_CCOEFF_NORMED)
    
            threshold = 0.96
            locations = np.where(result >= threshold)
            match_points = list(zip(*locations[::-1]))
    
            if len(match_points) > 0:
                print("未检测到继续指令，等待10秒...")
                sleep(10)
            else:
                print("检测到继续指令！")
                send_order = True
                return "育成结束，下一把"
                
        except Exception as e:
            print(f"检测异常: {str(e)}")
            sleep(5)  # 异常时稍作等待
            continue

def safe_perform_action(action):
    """带锁的执行操作"""
    with lock:
        perform_action(action)

def main():
    """主函数"""
    try:        
        # 初始化目标端口
        get_target_ports_once()
        
        if not target_ports:
            print("错误: 未能获取到任何目标端口")
            return
            
        # 初始化异步相关内容
        loop_thread = init_async()
        
        # 启动游戏状态检查
        game_thread = threading.Thread(target=check_game_state, daemon=True)
        game_thread.start()
        
        # 启动抓包
        while True:
            try:
                sniffer = start_capture()
                if sniffer:
                    sniffer.start()
                    sniffer.join()
                else:
                    sleep(3)
            except Exception as e:
                print(f"捕获异常: {str(e)}，3秒后重试...")
                sleep(3)
                
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"主程序异常: {str(e)}")
    finally:
        # 清理资源
        cleanup()

def cleanup():
    """清理资源"""
    global processing, loop
    
    print("开始清理资源...")
    
    # 停止处理
    processing = False
    
    # 停止事件循环
    if loop and not loop.is_closed():
        try:
            loop.call_soon_threadsafe(loop.stop)
            loop.close()
        except Exception as e:
            print(f"关闭事件循环时出错: {str(e)}")
    
    print("资源清理完成")

if __name__ == '__main__':
    main()
