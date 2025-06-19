import PyInstaller.__main__
import os
import sys
import shutil

print("🚀 开始打包 WorldQuant Brain Alpha Generator")
print("📦 版本: v2.0 - 智能参数配置 + 断点续传")
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
print("\n📦 开始PyInstaller打包...")
PyInstaller.__main__.run(args)

# 打包完成后，复制或创建配置文件到dist目录
print("\n📋 正在处理配置文件和文档...")
try:
    # 处理认证文件
    if os.path.exists('brain_credentials.txt'):
        shutil.copy2('brain_credentials.txt', 'dist/')
        print("✅ brain_credentials.txt 复制成功")
    else:
        # 创建示例认证文件
        with open('dist/brain_credentials.txt', 'w', encoding='utf-8') as f:
            f.write('["your_email@example.com","your_password"]')
        print("✅ 创建了示例 brain_credentials.txt")

    # 处理Alpha ID文件
    if os.path.exists('alpha_ids.txt'):
        shutil.copy2('alpha_ids.txt', 'dist/')
        print("✅ alpha_ids.txt 复制成功")
    else:
        # 创建空的alpha_ids.txt
        with open('dist/alpha_ids.txt', 'w', encoding='utf-8') as f:
            pass
        print("✅ 创建了空的 alpha_ids.txt")

    # 复制文档文件
    docs_to_copy = [
        'README.md',
        'SMART_CONFIG_GUIDE.md',
        'RESUME_GUIDE.md'
    ]

    for doc in docs_to_copy:
        if os.path.exists(doc):
            shutil.copy2(doc, 'dist/')
            print(f"✅ {doc} 复制成功")

    # 复制参数分析工具
    if os.path.exists('parameter_analysis.py'):
        shutil.copy2('parameter_analysis.py', 'dist/')
        print("✅ parameter_analysis.py 复制成功")

except Exception as e:
    print(f"❌ 处理配置文件时出错: {str(e)}")

print("\n🎉 打包完成！")
print("📁 输出目录: dist/")
print("🚀 主程序: Alpha_工具_v2.0")
print("📖 包含功能:")
print("   ✓ 智能参数配置系统")
print("   ✓ 智能断点续传功能")
print("   ✓ 参数配置效果分析")
print("   ✓ 完整使用文档")
print("\n💡 提示: 首次使用请先配置 brain_credentials.txt 文件")
