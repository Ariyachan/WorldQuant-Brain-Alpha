import PyInstaller.__main__
import os
import sys
import shutil

print("开始打包 WorldQuant Brain Alpha Generator")
print("版本: v2.0 - 智能参数配置 + 断点续传")
print("=" * 60)

# 确保目录存在
if not os.path.exists('dist'):
    os.makedirs('dist')

# 设置命令行参数
args = [
    'main.py',  # 主程序入口
    '--name=Alpha_工具_v2.0',  # 可执行文件名（更新版本号）
    '--onefile',  # 打包成单个文件
    '--console',  # 使用控制台窗口
    '--add-data=dataset_config.py{0}.'.format(os.pathsep),  # 添加配置文件
    '--add-data=alpha_strategy.py{0}.'.format(os.pathsep),  # 添加策略文件
    '--add-data=brain_batch_alpha.py{0}.'.format(os.pathsep),  # 添加核心处理文件（包含新功能）
    '--add-data=parameter_analysis.py{0}.'.format(os.pathsep),  # 添加参数分析工具
    '--clean',  # 清理临时文件
    '--noconfirm',  # 不确认覆盖
]

# 如果有图标文件，添加图标
if os.path.exists('icon.ico'):
    args.append('--icon=icon.ico')

# 运行打包命令
print("\n开始PyInstaller打包...")
PyInstaller.__main__.run(args)

# 打包完成后，复制或创建配置文件到dist目录
print("\n正在处理配置文件和文档...")
try:
    # 处理认证文件
    if os.path.exists('brain_credentials.txt'):
        shutil.copy2('brain_credentials.txt', 'dist/')
        print("brain_credentials.txt 复制成功")
    else:
        with open('dist/brain_credentials.txt', 'w', encoding='utf-8') as f:
            f.write('["your_email@example.com","your_password"]')
        print("创建了示例 brain_credentials.txt")

    # 处理Alpha ID文件
    if os.path.exists('alpha_ids.txt'):
        shutil.copy2('alpha_ids.txt', 'dist/')
        print("alpha_ids.txt 复制成功")
    else:
        with open('dist/alpha_ids.txt', 'w', encoding='utf-8') as f:
            pass
        print("创建了空的 alpha_ids.txt")

    # 复制文档文件
    docs_to_copy = [
        'README.md',
        'SMART_CONFIG_GUIDE.md',
        'RESUME_GUIDE.md'
    ]

    for doc in docs_to_copy:
        if os.path.exists(doc):
            shutil.copy2(doc, 'dist/')
            print(f"{doc} 复制成功")

    # 复制参数分析工具
    if os.path.exists('parameter_analysis.py'):
        shutil.copy2('parameter_analysis.py', 'dist/')
        print("parameter_analysis.py 复制成功")

    # 创建使用说明文件
    usage_content = """# WorldQuant Brain Alpha Generator v2.0 使用说明

## 🚀 新功能特性

### 1. 智能参数配置系统
- 自动识别Alpha表达式类型
- 智能选择最优参数组合
- 显著提高Alpha通过率

### 2. 智能断点续传功能
- 自动保存测试进度
- 智能跳过已测试表达式
- 支持Ctrl+C安全中断

## 📋 使用方法

1. 配置认证信息：编辑 brain_credentials.txt
2. 运行程序：双击 Alpha_工具_v2.0.exe
3. 选择运行模式和数据集
4. 等待自动测试和提交

## 🔄 断点续传

- 程序中断时自动保存进度
- 重新运行时自动从中断点继续
- 清除记录：选择模式4或运行时加 --clear-resume 参数

## 📊 参数分析

运行 parameter_analysis.py 查看参数配置效果分析

## 📖 详细文档

- README.md: 项目介绍
- SMART_CONFIG_GUIDE.md: 智能参数配置指南
- RESUME_GUIDE.md: 断点续传功能指南

## 🤝 技术支持

Email: 666@woaiys.filegear-sg.me
GitHub: https://github.com/YHYYDS666
"""

    with open('dist/使用说明.txt', 'w', encoding='utf-8') as f:
        f.write(usage_content)
    print("创建了使用说明.txt")

except Exception as e:
    print(f"处理配置文件时出错: {str(e)}")

print("\n打包完成！")
print("输出目录: dist/")
print("主程序: Alpha_工具_v2.0.exe")
print("包含功能:")
print("   智能参数配置系统")
print("   智能断点续传功能")
print("   参数配置效果分析")
print("   完整使用文档")
print("\n提示: 首次使用请先配置 brain_credentials.txt 文件")
