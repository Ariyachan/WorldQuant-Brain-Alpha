# 🚀 WorldQuant Brain Alpha Generator

<div align="center">

![GitHub stars](https://img.shields.io/github/stars/YHYYDS666/WorldQuant-Brain-Alpha?style=social)
![GitHub forks](https://img.shields.io/github/forks/YHYYDS666/WorldQuant-Brain-Alpha?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/YHYYDS666/WorldQuant-Brain-Alpha?style=social)

```txt
  ____    _____   _____    ____   _   _   _____ 
 |  _ \  |_   _| |  ___|  / ___| | | | | |_   _|
 | |_) |   | |   | |_    | |  _  | |_| |   | |  
 |  _ <    | |   |  _|   | |_| | |  _  |   | |  
 |_| \_\   |_|   |_|      \____| |_| |_|   |_|  
```

</div>

## 📖 项目介绍

这是一个用于自动生成和提交 WorldQuant Brain Alpha 表达式的工具。它可以帮助用户自动化测试和提交 Alpha 策略。

### 🧠 智能参数配置系统

本项目集成了智能参数配置系统，能够根据Alpha表达式的特征自动选择最优的模拟参数组合，显著提高Alpha通过率和性能指标。

### 🔄 智能断点续传功能

支持智能断点续传，当程序被中断时自动保存进度，下次运行时从中断点继续，避免重复测试，大幅提高开发效率。

## 🗂️ 目录结构

```txt
WorldQuant-Brain-Alpha/
├── 📜 main.py                # 主程序入口
├── 🧠 brain_batch_alpha.py   # 核心处理模块（智能参数配置）
├── 📊 alpha_strategy.py      # 策略生成模块
├── ⚙️ dataset_config.py      # 数据集配置
├── 📈 parameter_analysis.py  # 参数配置效果分析工具
├── 📋 requirements.txt       # 依赖列表
├── 🔨 build.py              # 通用构建脚本
├── 🪟 build_windows.py      # Windows构建脚本
├── 📦 setup.py              # 打包配置
├── 🗜️ create_zipapp.py      # ZIP打包脚本
└── 🍎 mac/                  # Mac相关文件
    ├── build_mac.py         # Mac构建脚本
    ├── create_icns.py       # 图标生成
    └── icon.png             # 图标源文件
```

## ✨ 功能特点

- 🤖 自动生成 Alpha 策略
- 🧠 智能参数配置优化
- 🔄 智能断点续传功能
- 📈 自动测试性能指标
- 🚀 自动提交合格策略
- 💾 保存策略 ID 和参数配置
- 🔄 支持多种运行模式
- 📊 参数配置效果分析

### 🎯 智能参数配置特性

- **表达式类型识别**: 自动识别日内、成交量、波动率、动量、均值回归、复杂策略等类型
- **参数自动优化**: 根据策略类型智能选择最优的Universe、Neutralization、Decay、Truncation参数
- **性能提升**: 显著提高Alpha通过率和性能指标
- **配置追踪**: 详细记录每个Alpha的参数配置和性能表现

### 🔄 智能断点续传特性

- **自动进度保存**: 程序中断时自动保存已测试的Alpha表达式记录
- **智能重复检测**: 启动时自动检查并跳过已测试的表达式
- **无缝恢复**: 从中断点继续执行，避免重复测试
- **灵活清理**: 支持清除历史记录，重新开始完整测试
- **Ctrl+C支持**: 优雅处理用户中断，确保进度不丢失

## 🛠️ 安装方法

上传文件出问题了，所有就分开放了两个版本。之后会合并成一个版本。

### Windows 用户

```bash
# 下载发布版本
✨ 从 Releases选择Alpha_Tool_v1.0版本 下载 Alpha_.zip

# 从源码构建
🔨 pip install -r requirements.txt
🚀 python build_windows.py
```

### Mac 用户

```bash
# 下载发布版本
✨ 从 Releases选择最新版 下载 Alpha_Tool_Mac.zip

  # 解压文件
  unzip Alpha_Tool_Mac.zip

  # 进入解压目录
  cd Alpha_Tool_Mac

  # 添加执行权限
  chmod +x Alpha_Tool

  # 运行程序
  ./Alpha_Tool

# 从源码构建
🔨 pip install -r requirements.txt
🚀 cd mac && python build_mac.py
```

## 📊 数据集支持

| 数据集 | 描述 | 股票范围 |
|--------|------|----------|
| 📈 fundamental6 | 基础财务数据 | TOP3000 |
| 📊 analyst4 | 分析师预测 | TOP1000 |
| 📉 pv1 | 成交量数据 | TOP1000 |

## 👍 性能要求

```txt
     ___________
    |  METRICS  |
    |-----------|
    | ✓ Sharpe  | > 1.5
    | ✓ Fitness | > 1.0
    | ✓ Turnover| 0.1-0.9
    | ✓ IC Mean | > 0.02
    |___________|
```

## 🎯 使用流程

1. 📝 配置账号信息
2. 🎲 选择数据集
3. 🔄 选择运行模式
4. 🧠 智能参数配置自动运行
5. 🔄 断点续传自动检查和跳过已测试表达式
6. 📊 等待结果生成
7. 🚀 自动提交策略

### 📈 参数配置分析

运行完成后，可以使用参数分析工具查看配置效果：

```bash
python parameter_analysis.py
```

该工具提供：
- 📊 各策略类型的性能统计
- 🏆 最佳参数组合分析
- 💡 参数优化建议

### 🔄 断点续传使用

**自动断点续传**：程序默认启用断点续传功能，无需额外配置

**手动清除记录**：
```bash
# 方式1：命令行参数
python main.py --clear-resume

# 方式2：交互式选择
python main.py
# 选择模式4：清除断点续传记录
```

**中断和恢复**：
- 运行过程中按 `Ctrl+C` 安全中断
- 下次运行自动从中断点继续
- 显示跳过的已测试表达式数量

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 👨‍💻 联系方式

- 📧 Email: <666@woaiys.filegear-sg.me>
- 🌟 GitHub: [YHYYDS666](https://github.com/YHYYDS666)

---

⭐ 如果这个项目帮助到你，请给一个 star! ⭐

## Star History

<a href="https://star-history.com/#WorldQuant-Brain-AlphaP/WorldQuant-Brain-AlphaP&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=WorldQuant-Brain-AlphaP/WorldQuant-Brain-AlphaP&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=WorldQuant-Brain-AlphaP/WorldQuant-Brain-AlphaP&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=WorldQuant-Brain-AlphaP/WorldQuant-Brain-AlphaP&type=Date" />
 </picture>
</a>
