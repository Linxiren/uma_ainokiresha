from InquirerPy import inquirer
import os
import sys
import importlib.util

def get_config_path():
    """获取程序运行目录"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def ensure_config_exists():
    """确保config.json存在，如果不存在则创建默认配置"""
    config_dir = get_config_path()
    config_path = os.path.join(config_dir, 'config.json')
    
    if not os.path.exists(config_path):
        default_config = {
            "ADB_PATH": "E:\\leidian\\LDPlayer9\\adb.exe",
            "DEVICE_ID": "emulator-5554",
            "TARGET_EXE": "E:\\凯旋门黑板\\UmaAi神经网络版（Nvidia显卡专属）.exe",
            "five_choice_one_action": "目标选择三",
            "use_alarm": "是",
            "min_vital_for_yellow_hat": 50.0,
            "skill_point_ratio": 50.0,
            "luck_thresholds": {
                "early": "-200",
                "mid": "10",
                "late": "300"
            },
            "filters": {
                "出道": {
                    "minFriendship": 35.0,
                    "minStatusSum": 1600.0,
                    "minlarc_supportPtAll": 13000.0
                },
                "第一次交流战前": {
                    "minFriendship": 71.0,
                    "minStatusSum": 2400.0,
                    "minlarc_supportPtAll": 30000.0
                },
                "继承": {
                    "minFriendship": 87.0,
                    "minStatusSum": 3700.0,
                    "minlarc_supportPtAll": 45000.0
                },
                "第二次交流战前": {
                    "minFriendship": 95.0,
                    "minStatusSum": 4500.0,
                    "minlarc_supportPtAll": 60000.0
                }
            },
            "normal_scores": {
                "速训练": 0.0,
                "耐训练": 0.0,
                "力训练": 0.0,
                "根训练": -20.0,
                "智训练": -50.0,
                "SS训练": 0.0,
                "休息": 0.0,
                "友人出行": 0.0,
                "单独出行": -60.0,
                "比赛": 0.0
            },
            "summer1_scores": {
                "速训练": 0.0,
                "耐训练": 0.0,
                "力训练": 0.0,
                "根训练": -35.0,
                "智训练": -90.0,
                "SS训练": 0.0,
                "休息": 0.0,
                "友人出行": 0.0,
                "单独出行": 0.0,
                "比赛": 0.0,
                "远征速": 0.0,
                "远征耐": 0.0,
                "远征力": 0.0,
                "远征根": -35.0,
                "远征智": -60.0
            },
            "summer2_scores": {
                "速训练": 0.0,
                "耐训练": 0.0,
                "力训练": 0.0,
                "根训练": -35.0,
                "智训练": -80.0,
                "SS训练": 0.0,
                "休息": -50.0,
                "友人出行": 0.0,
                "单独出行": 0.0,
                "比赛": 0.0,
                "远征速": 0.0,
                "远征耐": 0.0,
                "远征力": 0.0,
                "远征根": -45.0,
                "远征智": -100.0,
                "体速": 0.0,
                "体耐": 0.0,
                "体力": 0.0,
                "体根": 0.0,
                "体智": 0.0,
                "远征体速": 0.0,
                "远征体耐": 0.0,
                "远征体力": 0.0,
                "远征体根": -20.0,
                "远征体智": -180.0
            },
            "run_styles": {
                "逃": [43],
                "先": [39, 63],
                "差": [],
                "追": []
            }
        }
        import json
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"创建配置文件失败: {str(e)}")
            input("按任意键退出...")
            sys.exit(1)

def run_script(script_name):
    """导入并运行指定的脚本"""
    try:
        # 获取完整路径
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        script_path = os.path.join(base_path, script_name)
        
        # 设置配置文件路径
        os.environ['CONFIG_PATH'] = os.path.join(get_config_path(), 'config.json')
        
        # 导入并运行模块
        spec = importlib.util.spec_from_file_location(script_name, script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 如果模块有main函数则运行
        if hasattr(module, 'main'):
            module.main()
            
    except Exception as e:
        print(f"运行 {script_name} 时发生错误: {str(e)}")
        input("按任意键继续...")


def run_adb_and_jt():
    run_script('adb_control.py')
    run_script('jt.py')

def run_gui():
    run_script('gui.py')
    
def check_environment():
    run_script('check_npcap.py')

def main():
    ensure_config_exists()

    while True:
        try:
            menu_choice = inquirer.select(
                message="菜单(用↑和↓切换选项，回车确认，ctrl+c停止):",
                choices=["启动", "设置", "环境检查(第一次使用请先点这个，再点设置)", "退出"],
            ).execute()

            if menu_choice == "启动":
                run_adb_and_jt()
            elif menu_choice == "设置":
                run_gui()
            elif menu_choice == "环境检查(第一次使用请先点这个，再点设置)":
                check_environment()
            elif menu_choice == "退出":
                sys.exit(0)
        except KeyboardInterrupt:
            print("\n程序已停止")
            sys.exit(0)
        except Exception as e:
            print(f"发生错误: {str(e)}")
            input("按任意键继续...")

if __name__ == '__main__':
    main()
