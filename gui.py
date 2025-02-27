import gradio as gr
import json
import os
import sys

def get_config_path():
    """获取配置文件路径"""
    return os.getenv('CONFIG_PATH', 'config.json')

def save_config(
    adb_path, device_id, target_exe, five_choice_one_action,
    use_alarm, min_vital_for_yellow_hat, skill_point_ratio,
    luck_threshold_early, luck_threshold_mid, luck_threshold_late,
    filter1_min_friendship, filter1_min_status_sum, filter1_min_larc_support,
    filter2_min_friendship, filter2_min_status_sum, filter2_min_larc_support,
    filter3_min_friendship, filter3_min_status_sum, filter3_min_larc_support,
    filter4_min_friendship, filter4_min_status_sum, filter4_min_larc_support,
    normal_speed, normal_stamina, normal_power, normal_guts, normal_wisdom, normal_ss,
    normal_rest, normal_friend, normal_solo, normal_race,
    summer1_speed, summer1_stamina, summer1_power, summer1_guts, summer1_wisdom, summer1_ss,
    summer1_rest, summer1_friend, summer1_solo, summer1_race,
    summer1_exp_speed, summer1_exp_stamina, summer1_exp_power, summer1_exp_guts, summer1_exp_wisdom,
    summer2_speed, summer2_stamina, summer2_power, summer2_guts, summer2_wisdom, summer2_ss,
    summer2_rest, summer2_friend, summer2_solo, summer2_race,
    summer2_exp_speed, summer2_exp_stamina, summer2_exp_power, summer2_exp_guts, summer2_exp_wisdom,
    summer2_body_speed, summer2_body_stamina, summer2_body_power, summer2_body_guts, summer2_body_wisdom,
    summer2_exp_body_speed, summer2_exp_body_stamina, summer2_exp_body_power, summer2_exp_body_guts, summer2_exp_body_wisdom,
    run_style_escape, run_style_front, run_style_stalk, run_style_chase
):
    config = {
        "ADB_PATH": adb_path,
        "DEVICE_ID": device_id,
        "TARGET_EXE": target_exe,
        "five_choice_one_action": five_choice_one_action,
        "use_alarm": use_alarm,
        "min_vital_for_yellow_hat": min_vital_for_yellow_hat,
        "skill_point_ratio": skill_point_ratio,
        "luck_thresholds": {
            "early": luck_threshold_early,
            "mid": luck_threshold_mid,
            "late": luck_threshold_late
        },
        "filters": {
            "出道": {
                "minFriendship": filter1_min_friendship,
                "minStatusSum": filter1_min_status_sum,
                "minlarc_supportPtAll": filter1_min_larc_support
            },
            "第一次交流战前": {
                "minFriendship": filter2_min_friendship,
                "minStatusSum": filter2_min_status_sum,
                "minlarc_supportPtAll": filter2_min_larc_support
            },
            "继承": {
                "minFriendship": filter3_min_friendship,
                "minStatusSum": filter3_min_status_sum,
                "minlarc_supportPtAll": filter3_min_larc_support
            },
            "第二次交流战前": {
                "minFriendship": filter4_min_friendship,
                "minStatusSum": filter4_min_status_sum,
                "minlarc_supportPtAll": filter4_min_larc_support
            }
        },
        "normal_scores": {
            "速训练": normal_speed, "耐训练": normal_stamina, "力训练": normal_power,
            "根训练": normal_guts, "智训练": normal_wisdom, "SS训练": normal_ss,
            "休息": normal_rest, "友人出行": normal_friend, "单独出行": normal_solo,
            "比赛": normal_race
        },
        "summer1_scores": {
            "速训练": summer1_speed, "耐训练": summer1_stamina, "力训练": summer1_power,
            "根训练": summer1_guts, "智训练": summer1_wisdom, "SS训练": summer1_ss,
            "休息": summer1_rest, "友人出行": summer1_friend, "单独出行": summer1_solo,
            "比赛": summer1_race,
            "远征速": summer1_exp_speed, "远征耐": summer1_exp_stamina, "远征力": summer1_exp_power,
            "远征根": summer1_exp_guts, "远征智": summer1_exp_wisdom
        },
        "summer2_scores": {
            "速训练": summer2_speed, "耐训练": summer2_stamina, "力训练": summer2_power,
            "根训练": summer2_guts, "智训练": summer2_wisdom, "SS训练": summer2_ss,
            "休息": summer2_rest, "友人出行": summer2_friend, "单独出行": summer2_solo,
            "比赛": summer2_race,
            "远征速": summer2_exp_speed, "远征耐": summer2_exp_stamina, "远征力": summer2_exp_power,
            "远征根": summer2_exp_guts, "远征智": summer2_exp_wisdom,
            "体速": summer2_body_speed, "体耐": summer2_body_stamina, "体力": summer2_body_power,
            "体根": summer2_body_guts, "体智": summer2_body_wisdom,
            "远征体速": summer2_exp_body_speed, "远征体耐": summer2_exp_body_stamina,
            "远征体力": summer2_exp_body_power, "远征体根": summer2_exp_body_guts,
            "远征体智": summer2_exp_body_wisdom
        },
        "run_styles": {
            "逃": list(map(int, run_style_escape.split(','))) if run_style_escape else [],
            "先": list(map(int, run_style_front.split(','))) if run_style_front else [],
            "差": list(map(int, run_style_stalk.split(','))) if run_style_stalk else [],
            "追": list(map(int, run_style_chase.split(','))) if run_style_chase else [],
        }
    }
    with open(get_config_path(), 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    return "设置已保存"

def load_config():
    try:
        with open(get_config_path(), 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        filters = config.get("filters", {})
        luck_thresholds = config.get("luck_thresholds", {})
        normal = config.get("normal_scores", {})
        ss = config.get("ss_scores", {})
        summer1 = config.get("summer1_scores", {})
        summer2 = config.get("summer2_scores", {})

        return [
            config.get("ADB_PATH", ""),
            config.get("DEVICE_ID", ""),
            config.get("TARGET_EXE", ""),
            config.get("five_choice_one_action", "目标选择三"),
            config.get("use_alarm", "否"),
            config.get("min_vital_for_yellow_hat", 0),
            config.get("skill_point_ratio", 0),
            luck_thresholds.get("early", ""),
            luck_thresholds.get("mid", ""),
            luck_thresholds.get("late", ""),
            filters.get("出道", {}).get("minFriendship", 0),
            filters.get("出道", {}).get("minStatusSum", 0),
            filters.get("出道", {}).get("minlarc_supportPtAll", 0),
            filters.get("第一次交流战前", {}).get("minFriendship", 0),
            filters.get("第一次交流战前", {}).get("minStatusSum", 0),
            filters.get("第一次交流战前", {}).get("minlarc_supportPtAll", 0),
            filters.get("继承", {}).get("minFriendship", 0),
            filters.get("继承", {}).get("minStatusSum", 0),
            filters.get("继承", {}).get("minlarc_supportPtAll", 0),
            filters.get("第二次交流战前", {}).get("minFriendship", 0),
            filters.get("第二次交流战前", {}).get("minStatusSum", 0),
            filters.get("第二次交流战前", {}).get("minlarc_supportPtAll", 0),
            normal.get("速训练", 0), normal.get("耐训练", 0), normal.get("力训练", 0),
            normal.get("根训练", -20), normal.get("智训练", -50), normal.get("SS训练", 0),
            normal.get("休息", 0), normal.get("友人出行", 0), normal.get("单独出行", -60),
            normal.get("比赛", 0),
            summer1.get("速训练", 0), summer1.get("耐训练", 0), summer1.get("力训练", 0),
            summer1.get("根训练", -35), summer1.get("智训练", -90), summer1.get("SS训练", 0),
            summer1.get("休息", 0), summer1.get("友人出行", 0), summer1.get("单独出行", 0),
            summer1.get("比赛", 0),
            summer1.get("远征速", 0), summer1.get("远征耐", 0), summer1.get("远征力", 0),
            summer1.get("远征根", -35), summer1.get("远征智", -60),
            summer2.get("速训练", 0), summer2.get("耐训练", 0), summer2.get("力训练", 0),
            summer2.get("根训练", -35), summer2.get("智训练", -80), summer2.get("SS训练", 0),
            summer2.get("休息", -50), summer2.get("友人出行", 0), summer2.get("单独出行", 0),
            summer2.get("比赛", 0),
            summer2.get("远征速", 0), summer2.get("远征耐", 0), summer2.get("远征力", 0),
            summer2.get("远征根", -45), summer2.get("远征智", -100),
            summer2.get("体速", 0), summer2.get("体耐", 0), summer2.get("体力", 0),
            summer2.get("体根", 0), summer2.get("体智", 0),
            summer2.get("远征体速", 0), summer2.get("远征体耐", 0), summer2.get("远征体力", 0),
            summer2.get("远征体根", -20), summer2.get("远征体智", -180),
            ','.join(map(str, config.get("run_styles", {}).get("逃", []))),
            ','.join(map(str, config.get("run_styles", {}).get("先", []))),
            ','.join(map(str, config.get("run_styles", {}).get("差", []))),
            ','.join(map(str, config.get("run_styles", {}).get("追", [])))
        ]
    except FileNotFoundError:
        return [""] * 86  # 新增的22个参数加上原有的59个参数

def create_number_box(label, value=0):
    return gr.Number(label=label, value=value)

with gr.Blocks() as demo:
    gr.Markdown("# 爱脚本设置（第一次打开后请务必保存设置。不管更改了什么，都请点击保存设置再关闭）")
    
    with gr.Row():
        adb_path = gr.Textbox(label="雷电九的adb位置（除非已经会了，否则请务必看使用说明.pdf）")
        device_id = gr.Textbox(label="模拟器设备号（正常来说填emulator-5554即可，但还是推荐先看使用说明.pdf）")
    
    target_exe = gr.Textbox(label="umaai的位置（除非已经会了，否则请务必看使用说明.pdf）")
    
    with gr.Row():
        five_choice_one_action = gr.Dropdown(
            choices=["目标选择一", "目标选择二", "目标选择三", "目标选择四", "目标选择五"],
            value="目标选择三",
            label="经典年一月下目标选择"
        )
        use_alarm = gr.Dropdown(
            choices=["是", "否"],
            value="否",
            label="是否使用闹钟"
        )
    
    with gr.Row():
        min_vital_for_yellow_hat = create_number_box("允许在体力低于多少的时候赌黄帽出行事件选择二", 0)
        skill_point_ratio = create_number_box("一点技能点可以以多大倍率计入总属性（单位:%）", 0)
    
    with gr.Row():
        luck_threshold_early = gr.Textbox(label="本局运气指标低于多少就立刻放弃(1-5回合)")
        luck_threshold_mid = gr.Textbox(label="本局运气指标低于多少就立刻放弃(6-11回合)")
        luck_threshold_late = gr.Textbox(label="本局运气指标低于多少就立刻放弃(13-23回合)")

    with gr.Tabs():
        with gr.TabItem("第一过滤器(出道)"):
            with gr.Group():
                filter1_min_friendship = create_number_box("允许的支援卡最低友情度", 0)
                filter1_min_status_sum = create_number_box("允许的最低总属性", 0)
                filter1_min_larc_support = create_number_box("允许的最低总期待度", 0)
        
        with gr.TabItem("第二过滤器(第一次交流战前)"):
            with gr.Group():
                filter2_min_friendship = create_number_box("允许的支援卡最低友情度", 0)
                filter2_min_status_sum = create_number_box("允许的最低总属性", 0)
                filter2_min_larc_support = create_number_box("允许的最低总期待度", 0)
        
        with gr.TabItem("第三过滤器(继承)"):
            with gr.Group():
                filter3_min_friendship = create_number_box("允许的支援卡最低友情度", 0)
                filter3_min_status_sum = create_number_box("允许的最低总属性", 0)
                filter3_min_larc_support = create_number_box("允许的最低总期待度", 0)
        
        with gr.TabItem("第四过滤器(第二次交流战前)"):
            with gr.Group():
                filter4_min_friendship = create_number_box("允许的支援卡最低友情度", 0)
                filter4_min_status_sum = create_number_box("允许的最低总属性", 0)
                filter4_min_larc_support = create_number_box("允许的最低总期待度", 0)

    with gr.Tabs():
        with gr.TabItem("调整平时训练分数"):
            with gr.Group():
                normal_speed = create_number_box("速训练")
                normal_stamina = create_number_box("耐训练")
                normal_power = create_number_box("力训练")
                normal_guts = create_number_box("根训练", -20)
                normal_wisdom = create_number_box("智训练", -50)
                normal_ss = create_number_box("SS训练")
                normal_rest = create_number_box("休息")
                normal_friend = create_number_box("友人出行")
                normal_solo = create_number_box("单独出行", -60)
                normal_race = create_number_box("比赛")
        
        with gr.TabItem("调整第一次远征训练分数"):
            with gr.Group():
                summer1_speed = create_number_box("速训练")
                summer1_stamina = create_number_box("耐训练")
                summer1_power = create_number_box("力训练")
                summer1_guts = create_number_box("根训练", -35)
                summer1_wisdom = create_number_box("智训练", -90)
                summer1_ss = create_number_box("SS训练")
                summer1_rest = create_number_box("休息")
                summer1_friend = create_number_box("友人出行")
                summer1_solo = create_number_box("单独出行")
                summer1_race = create_number_box("比赛")
                summer1_exp_speed = create_number_box("远征速")
                summer1_exp_stamina = create_number_box("远征耐")
                summer1_exp_power = create_number_box("远征力")
                summer1_exp_guts = create_number_box("远征根", -35)
                summer1_exp_wisdom = create_number_box("远征智", -60)
        
        with gr.TabItem("调整第二次远征训练分数"):
            with gr.Group():
                summer2_speed = create_number_box("速训练")
                summer2_stamina = create_number_box("耐训练")
                summer2_power = create_number_box("力训练")
                summer2_guts = create_number_box("根训练", -35)
                summer2_wisdom = create_number_box("智训练", -80)
                summer2_ss = create_number_box("SS训练")
                summer2_rest = create_number_box("休息", -50)
                summer2_friend = create_number_box("友人出行")
                summer2_solo = create_number_box("单独出行")
                summer2_race = create_number_box("比赛")
                summer2_exp_speed = create_number_box("远征速")
                summer2_exp_stamina = create_number_box("远征耐")
                summer2_exp_power = create_number_box("远征力")
                summer2_exp_guts = create_number_box("远征根", -45)
                summer2_exp_wisdom = create_number_box("远征智", -100)
                summer2_body_speed = create_number_box("体速")
                summer2_body_stamina = create_number_box("体耐")
                summer2_body_power = create_number_box("体力")
                summer2_body_guts = create_number_box("体根")
                summer2_body_wisdom = create_number_box("体智")
                summer2_exp_body_speed = create_number_box("远征体速")
                summer2_exp_body_stamina = create_number_box("远征体耐")
                summer2_exp_body_power = create_number_box("远征体力")
                summer2_exp_body_guts = create_number_box("远征体根", -20)
                summer2_exp_body_wisdom = create_number_box("远征体智", -180)

    with gr.Row():
        run_style_escape = gr.Textbox(label="逃跑法回合数")
        run_style_front = gr.Textbox(label="先跑法回合数")
        run_style_stalk = gr.Textbox(label="差跑法回合数")
        run_style_chase = gr.Textbox(label="追跑法回合数")
    
    save_button = gr.Button("保存设置")
    load_button = gr.Button("加载设置")
    
    save_button.click(
        save_config,
        inputs=[
            adb_path, device_id, target_exe, five_choice_one_action,
            use_alarm, min_vital_for_yellow_hat, skill_point_ratio,
            luck_threshold_early, luck_threshold_mid, luck_threshold_late,
            filter1_min_friendship, filter1_min_status_sum, filter1_min_larc_support,
            filter2_min_friendship, filter2_min_status_sum, filter2_min_larc_support,
            filter3_min_friendship, filter3_min_status_sum, filter3_min_larc_support,
            filter4_min_friendship, filter4_min_status_sum, filter4_min_larc_support,
            normal_speed, normal_stamina, normal_power, normal_guts, normal_wisdom, normal_ss,
            normal_rest, normal_friend, normal_solo, normal_race,
            summer1_speed, summer1_stamina, summer1_power, summer1_guts, summer1_wisdom, summer1_ss,
            summer1_rest, summer1_friend, summer1_solo, summer1_race,
            summer1_exp_speed, summer1_exp_stamina, summer1_exp_power, summer1_exp_guts, summer1_exp_wisdom,
            summer2_speed, summer2_stamina, summer2_power, summer2_guts, summer2_wisdom, summer2_ss,
            summer2_rest, summer2_friend, summer2_solo, summer2_race,
            summer2_exp_speed, summer2_exp_stamina, summer2_exp_power, summer2_exp_guts, summer2_exp_wisdom,
            summer2_body_speed, summer2_body_stamina, summer2_body_power, summer2_body_guts, summer2_body_wisdom,
            summer2_exp_body_speed, summer2_exp_body_stamina, summer2_exp_body_power, summer2_exp_body_guts, summer2_exp_body_wisdom,
            run_style_escape, run_style_front, run_style_stalk, run_style_chase
        ],
        outputs=gr.Textbox(label="保存状态")
    )
    
    load_button.click(
        load_config,
        outputs=[
            adb_path, device_id, target_exe, five_choice_one_action,
            use_alarm, min_vital_for_yellow_hat, skill_point_ratio,
            luck_threshold_early, luck_threshold_mid, luck_threshold_late,
            filter1_min_friendship, filter1_min_status_sum, filter1_min_larc_support,
            filter2_min_friendship, filter2_min_status_sum, filter2_min_larc_support,
            filter3_min_friendship, filter3_min_status_sum, filter3_min_larc_support,
            filter4_min_friendship, filter4_min_status_sum, filter4_min_larc_support,
            normal_speed, normal_stamina, normal_power, normal_guts, normal_wisdom, normal_ss,
            normal_rest, normal_friend, normal_solo, normal_race,
            summer1_speed, summer1_stamina, summer1_power, summer1_guts, summer1_wisdom, summer1_ss,
            summer1_rest, summer1_friend, summer1_solo, summer1_race,
            summer1_exp_speed, summer1_exp_stamina, summer1_exp_power, summer1_exp_guts, summer1_exp_wisdom,
            summer2_speed, summer2_stamina, summer2_power, summer2_guts, summer2_wisdom, summer2_ss,
            summer2_rest, summer2_friend, summer2_solo, summer2_race,
            summer2_exp_speed, summer2_exp_stamina, summer2_exp_power, summer2_exp_guts, summer2_exp_wisdom,
            summer2_body_speed, summer2_body_stamina, summer2_body_power, summer2_body_guts, summer2_body_wisdom,
            summer2_exp_body_speed, summer2_exp_body_stamina, summer2_exp_body_power, summer2_exp_body_guts, summer2_exp_body_wisdom,
            run_style_escape, run_style_front, run_style_stalk, run_style_chase
        ]
    )

def main():
    demo.launch(inbrowser=True)

if __name__ == '__main__':
    main()
