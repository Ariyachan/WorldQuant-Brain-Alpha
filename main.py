"""WorldQuant Brain 批量 Alpha 生成系统 - 支持智能断点续传"""

import os
import sys

from brain_batch_alpha import BrainBatchAlpha
from dataset_config import get_dataset_by_index, get_dataset_list

STORAGE_ALPHA_ID_PATH = "alpha_ids.txt"


def submit_alpha_ids(brain, num_to_submit=2):
    """提交保存的 Alpha ID"""
    try:
        if not os.path.exists(STORAGE_ALPHA_ID_PATH):
            print("❌ 没有找到保存的Alpha ID文件")
            return

        with open(STORAGE_ALPHA_ID_PATH, 'r') as f:
            alpha_ids = [line.strip() for line in f.readlines() if line.strip()]

        if not alpha_ids:
            print("❌ 没有可提交的Alpha ID")
            return

        print("\n📝 已保存的Alpha ID列表:")
        for i, alpha_id in enumerate(alpha_ids, 1):
            print(f"{i}. {alpha_id}")

        if num_to_submit > len(alpha_ids):
            num_to_submit = len(alpha_ids)

        selected_ids = alpha_ids[:num_to_submit]
        successful, failed = brain.submit_multiple_alphas(selected_ids)

        # 更新 alpha_ids.txt
        remaining_ids = [id for id in alpha_ids if id not in successful]
        with open(STORAGE_ALPHA_ID_PATH, 'w') as f:
            f.writelines([f"{id}\n" for id in remaining_ids])

    except Exception as e:
        print(f"❌ 提交 Alpha 时出错: {str(e)}")


def main():
    """主程序入口"""
    try:
        # 检查命令行参数
        if len(sys.argv) > 1 and sys.argv[1] == '--clear-resume':
            brain = BrainBatchAlpha()
            brain.clear_resume_data()
            return

        print("🚀 启动 WorldQuant Brain 批量 Alpha 生成系统")
        print("🧠 智能参数配置 + 断点续传功能已启用")

        # 显示断点续传状态
        brain = BrainBatchAlpha()
        stats = brain.get_resume_stats()
        if stats['total_tested'] > 0:
            print(f"📊 断点续传状态: 已有 {stats['total_tested']} 个测试记录")
            print("💡 提示: 程序将自动跳过已测试的Alpha表达式")
            print("🗑️ 如需重新开始，请运行: python main.py --clear-resume")

        print("\n📋 请选择运行模式:")
        print("1: 自动模式 (测试并自动提交 2 个合格 Alpha)")
        print("2: 仅测试模式 (测试并保存合格 Alpha ID)")
        print("3: 仅提交模式 (提交已保存的合格 Alpha ID)")
        print("4: 清除断点续传记录")

        mode = int(input("\n请选择模式 (1-4): "))
        if mode not in [1, 2, 3, 4]:
            print("❌ 无效的模式选择")
            return

        if mode in [1, 2]:
            print("\n📊 可用数据集列表:")
            for dataset in get_dataset_list():
                print(dataset)

            dataset_index = input("\n请选择数据集编号: ")
            dataset_name = get_dataset_by_index(dataset_index)
            if not dataset_name:
                print("❌ 无效的数据集编号")
                return

            print("\n📈 可用策略模式:")
            print("1: 基础策略模式")
            print("2: 多因子组合模式")

            strategy_mode = int(input("\n请选择策略模式 (1-2): "))
            if strategy_mode not in [1, 2]:
                print("❌ 无效的策略模式")
                return

            print("\n🔄 开始Alpha模拟（支持Ctrl+C中断和断点续传）...")
            try:
                results = brain.simulate_alphas(None, strategy_mode, dataset_name)

                if mode == 1:
                    submit_alpha_ids(brain, 2)

            except KeyboardInterrupt:
                print("\n⚠️ 用户中断操作")
                print("💾 进度已自动保存，下次运行将从中断点继续")
                return

        elif mode == 3:
            num_to_submit = int(input("\n请输入要提交的 Alpha 数量: "))
            if num_to_submit <= 0:
                print("❌ 无效的提交数量")
                return
            submit_alpha_ids(brain, num_to_submit)

        elif mode == 4:
            confirm = input("\n⚠️ 确认清除所有断点续传记录？(y/N): ")
            if confirm.lower() == 'y':
                brain.clear_resume_data()
            else:
                print("❌ 操作已取消")

    except KeyboardInterrupt:
        print("\n⚠️ 程序被用户中断")
    except Exception as e:
        print(f"❌ 程序运行出错: {str(e)}")


if __name__ == "__main__":
    main()
