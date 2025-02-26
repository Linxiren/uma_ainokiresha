import os
import sys
import webbrowser

def check_npcap():
    """检查是否安装了Npcap"""
    npcap_paths = [
        "C:\\Program Files\\Npcap",
        "C:\\Windows\\System32\\Npcap",
        "C:\\Program Files (x86)\\Npcap"
    ]
    return any(os.path.exists(path) for path in npcap_paths)

def guide_wireshark_installation():
    """引导用户安装Wireshark"""
    print("\n需要安装 Wireshark 来获取必要的网络组件。")
    print("\n请按照以下步骤操作：")
    print("1. 在弹出的网页中下载 Wireshark")
    print("2. 运行下载的安装程序")
    print("3. 在安装过程中，请确保勾选 \"Install Npcap\" 选项，这是一个单独勾选的页面，前面还有几个可勾选选项的页面，反正全部默认就行，Npcap安装界面也全部默认")
    print("4. 完成安装后返回此窗口")
    
    choice = input("\n是否现在打开 Wireshark 下载页面？(y/n): ")
    if choice.lower() == 'y':
        # 打开Wireshark下载页面
        webbrowser.open('https://www.wireshark.org/download.html')
    else:
        print("\n您可以稍后访问 https://www.wireshark.org/download.html 下载安装")
    
    print("\n请在完成 Wireshark 安装后按回车键继续...")
    input()

def main():
    """主函数"""
    if check_npcap():
        print("检测到 Npcap 已安装。")
        input("\n按任意键继续...")
        return True
    
    print("未检测到 Npcap，需要安装 Wireshark 才能继续。")
    choice = input("是否立即安装 Wireshark？(y/n): ")
    
    if choice.lower() != 'y':
        print("取消安装。程序可能无法正常工作。")
        input("\n按任意键继续...")
        return False
    
    guide_wireshark_installation()
    
    # 安装后再次检查
    if check_npcap():
        print("Npcap 安装成功！")
        input("\n按任意键继续...")
        return True
    else:
        print("\n未检测到 Npcap，请确保在安装 Wireshark 时选中了 \"Install Npcap\" 选项。")
        print("您可以：")
        print("1. 重新运行 Wireshark 安装程序并确保选中 Npcap")
        print("2. 或访问 https://www.wireshark.org/download.html 重新下载安装")
        input("\n按任意键继续...")
        return False

if __name__ == "__main__":
    main()