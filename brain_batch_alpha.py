"""WorldQuant Brain API 批量处理模块 - 智能参数配置+断点续传优化版本"""

import hashlib
import json
import os
import random
import re
import signal
import sys
from datetime import datetime
from os.path import expanduser
from time import sleep

import pandas as pd
import requests
from requests.auth import HTTPBasicAuth

from alpha_strategy import AlphaStrategy
from dataset_config import get_api_settings, get_dataset_config


class ResumeManager:
    """智能断点续传管理器"""

    def __init__(self, resume_file="alpha_resume.json"):
        """初始化断点续传管理器"""
        self.resume_file = resume_file
        self.tested_expressions = self._load_tested_expressions()
        self.current_session_tested = set()
        self.interrupted = False

        # 设置信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """处理中断信号"""
        print(f"\n\n检测到中断信号 ({signum})，正在保存进度...")
        self.interrupted = True
        self._save_tested_expressions()
        print("进度已保存，下次运行将从中断点继续")
        print("如需重新开始完整测试，请运行: python main.py --clear-resume")
        sys.exit(0)

    def _load_tested_expressions(self):
        """加载已测试的表达式记录"""
        if not os.path.exists(self.resume_file):
            return {}

        try:
            with open(self.resume_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"加载断点续传记录: {len(data)} 个已测试表达式")
                return data
        except Exception as e:
            print(f"⚠️ 加载断点续传记录失败: {str(e)}")
            return {}

    def _save_tested_expressions(self):
        """保存已测试的表达式记录"""
        try:
            with open(self.resume_file, 'w', encoding='utf-8') as f:
                json.dump(self.tested_expressions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 保存断点续传记录失败: {str(e)}")

    def get_expression_hash(self, expression, parameters=None):
        """生成表达式的唯一哈希标识"""
        # 组合表达式和关键参数生成哈希
        content = expression
        if parameters:
            # 只包含影响结果的关键参数
            key_params = {
                'universe': parameters.get('universe'),
                'neutralization': parameters.get('neutralization'),
                'decay': parameters.get('decay'),
                'truncation': parameters.get('truncation')
            }
            content += str(sorted(key_params.items()))

        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def is_expression_tested(self, expression, parameters=None):
        """检查表达式是否已经测试过"""
        expr_hash = self.get_expression_hash(expression, parameters)
        return expr_hash in self.tested_expressions

    def mark_expression_tested(self, expression, parameters=None, result=None):
        """标记表达式为已测试"""
        expr_hash = self.get_expression_hash(expression, parameters)
        self.tested_expressions[expr_hash] = {
            'expression': expression,
            'parameters': parameters or {},
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'result': result or {}
        }
        self.current_session_tested.add(expr_hash)

        # 定期保存（每10个表达式保存一次）
        if len(self.current_session_tested) % 10 == 0:
            self._save_tested_expressions()

    def get_resume_stats(self):
        """获取断点续传统计信息"""
        return {
            'total_tested': len(self.tested_expressions),
            'session_tested': len(self.current_session_tested)
        }

    def clear_resume_data(self):
        """清除断点续传数据"""
        if os.path.exists(self.resume_file):
            os.remove(self.resume_file)
            print(f"已清除断点续传记录: {self.resume_file}")
        self.tested_expressions = {}
        self.current_session_tested = set()

    def filter_untested_alphas(self, alpha_list):
        """过滤出未测试的alpha表达式"""
        untested_alphas = []
        skipped_count = 0

        print("检查断点续传记录...")

        for alpha in alpha_list:
            expression = alpha.get('regular', '')
            parameters = alpha.get('settings', {})

            if self.is_expression_tested(expression, parameters):
                skipped_count += 1
            else:
                untested_alphas.append(alpha)

        if skipped_count > 0:
            print(f"跳过 {skipped_count} 个已测试的Alpha表达式")
            print(f"继续测试 {len(untested_alphas)} 个未测试的Alpha表达式")
        else:
            print(f"所有 {len(untested_alphas)} 个Alpha表达式都是新的")

        return untested_alphas, skipped_count

    def finalize_session(self):
        """结束会话，保存最终状态"""
        if not self.interrupted:
            self._save_tested_expressions()
            stats = self.get_resume_stats()
            print(f"\n会话结束，已保存 {stats['session_tested']} 个新测试记录")
            print(f"累计测试记录: {stats['total_tested']} 个Alpha表达式")


class SmartParameterOptimizer:
    """智能模拟参数配置器"""

    def __init__(self):
        """初始化参数配置器"""

        # 可选参数范围定义
        self.universe_options = ['TOP3000', 'TOP1000', 'TOP500', 'TOP200', 'TOPSP500']
        self.neutralization_options = [None, 'MARKET', 'SECTOR', 'INDUSTRY', 'SUBINDUSTRY']
        self.decay_range = (0, 20)
        self.truncation_range = (0.01, 0.15)

        # 基于表达式类型的参数优化规则
        self.optimization_rules = {
            'intraday': {  # 日内策略
                'universe': ['TOP1000', 'TOP500'],
                'neutralization': ['SUBINDUSTRY', 'INDUSTRY'],
                'decay': (0, 5),
                'truncation': (0.05, 0.10)
            },
            'volume': {  # 成交量策略
                'universe': ['TOP3000', 'TOP1000'],
                'neutralization': ['MARKET', 'SECTOR'],
                'decay': (2, 8),
                'truncation': (0.06, 0.12)
            },
            'volatility': {  # 波动率策略
                'universe': ['TOP3000', 'TOP1000'],
                'neutralization': ['SUBINDUSTRY', 'INDUSTRY'],
                'decay': (5, 15),
                'truncation': (0.04, 0.08)
            },
            'momentum': {  # 动量策略
                'universe': ['TOP1000', 'TOP500'],
                'neutralization': ['INDUSTRY', 'SECTOR'],
                'decay': (3, 10),
                'truncation': (0.07, 0.12)
            },
            'mean_reversion': {  # 均值回归策略
                'universe': ['TOP3000', 'TOP1000'],
                'neutralization': ['SUBINDUSTRY', 'MARKET'],
                'decay': (1, 6),
                'truncation': (0.05, 0.10)
            },
            'complex': {  # 复杂策略
                'universe': ['TOP1000', 'TOP500'],
                'neutralization': ['SUBINDUSTRY', 'INDUSTRY'],
                'decay': (8, 18),
                'truncation': (0.03, 0.07)
            },
            'default': {  # 默认策略
                'universe': ['TOP3000', 'TOP1000'],
                'neutralization': ['SUBINDUSTRY', 'INDUSTRY'],
                'decay': (0, 10),
                'truncation': (0.05, 0.10)
            }
        }

    def analyze_expression_type(self, expression):
        """分析alpha表达式类型"""

        expression_lower = expression.lower()

        # 日内策略检测
        if any(keyword in expression_lower for keyword in ['open', 'close', 'high', 'low', '(close - open)', '(open - delay']):
            return 'intraday'

        # 成交量策略检测
        if any(keyword in expression_lower for keyword in ['volume', 'turnover', 'sharesout']):
            return 'volume'

        # 波动率策略检测
        if any(keyword in expression_lower for keyword in ['std_dev', 'volatility', 'ts_std_dev', 'power(']):
            return 'volatility'

        # 动量策略检测
        if any(keyword in expression_lower for keyword in ['ts_rank', 'rank(', 'correlation', 'ts_corr']):
            return 'momentum'

        # 均值回归策略检测
        if any(keyword in expression_lower for keyword in ['mean(', 'group_mean', 'ts_mean', 'delay(']):
            return 'mean_reversion'

        # 复杂策略检测
        if any(keyword in expression_lower for keyword in ['regression_neut', 'vector_neut', 'trade_when', 'if_else']):
            return 'complex'

        return 'default'

    def get_optimal_parameters(self, expression, dataset_universe=None):
        """为给定表达式获取最优参数配置"""

        expr_type = self.analyze_expression_type(expression)
        rules = self.optimization_rules.get(expr_type, self.optimization_rules['default'])

        # Universe参数约束：如果指定了数据集Universe，则强制使用
        if dataset_universe:
            universe = dataset_universe
        else:
            # 如果没有数据集约束，则使用智能配置
            universe = random.choice(rules['universe'])

        # 其他参数仍然使用智能配置
        neutralization = random.choice(rules['neutralization'])
        decay = random.randint(rules['decay'][0], rules['decay'][1])
        truncation = round(random.uniform(rules['truncation'][0], rules['truncation'][1]), 3)

        return {
            'universe': universe,
            'neutralization': neutralization,
            'decay': decay,
            'truncation': truncation,
            'expression_type': expr_type
        }


class BrainBatchAlpha:
    # 尝试不同的API基础URL
    API_BASE_URLS = [
        'https://api.worldquantbrain.com',
        'https://platform.worldquantbrain.com/api',
        'https://brain.worldquant.com/api'
    ]

    def __init__(self, credentials_file='brain_credentials.txt', enable_resume=True):
        """初始化 API 客户端"""

        self.session = requests.Session()
        self.parameter_optimizer = SmartParameterOptimizer()
        self.resume_manager = ResumeManager() if enable_resume else None
        self.API_BASE_URL = None  # 将在认证时确定
        self._setup_authentication(credentials_file)



    def _setup_authentication(self, credentials_file):
        """设置认证 - 尝试多个API端点"""

        try:
            with open(expanduser(credentials_file)) as f:
                credentials = json.load(f)
            username, password = credentials
            self.session.auth = HTTPBasicAuth(username, password)

            # 设置请求头
            self.session.headers.update({
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'WorldQuant-Brain-Alpha-Generator/2.0'
            })

            print(f"尝试认证用户: {username}")

            # 尝试不同的API基础URL和认证端点
            auth_endpoints = ['/authentication', '/auth', '/login']

            for base_url in self.API_BASE_URLS:
                for auth_endpoint in auth_endpoints:
                    full_url = base_url + auth_endpoint

                    print(f"尝试认证端点: {full_url}")

                    try:
                        response = self.session.post(full_url, timeout=10)

                        print(f"  状态码: {response.status_code}")

                        if response.status_code in [200, 201]:
                            print("认证成功!")
                            self.API_BASE_URL = base_url
                            return
                        elif response.status_code == 400:
                            print(f"  400错误: {response.text[:200]}")
                        elif response.status_code == 401:
                            print("  401错误: 认证失败，请检查用户名密码")
                        elif response.status_code == 404:
                            print("  404错误: 端点不存在")
                        else:
                            print(f"  其他错误: {response.status_code}")

                    except requests.exceptions.RequestException as e:
                        print(f"  请求异常: {str(e)}")
                        continue

            # 如果所有端点都失败，使用默认URL并继续
            print("警告: 所有认证端点都失败，使用默认API URL继续")
            self.API_BASE_URL = self.API_BASE_URLS[0]

        except Exception as e:
            print(f"认证错误: {str(e)}")
            # 不抛出异常，使用默认URL继续
            self.API_BASE_URL = self.API_BASE_URLS[0]

    def simulate_alphas(self, datafields=None, strategy_mode=1, dataset_name=None):
        """模拟 Alpha 列表 - 支持断点续传"""

        try:
            datafields = self._get_datafields_if_none(datafields, dataset_name)
            if not datafields:
                return []

            alpha_list = self._generate_alpha_list(datafields, strategy_mode, dataset_name)
            if not alpha_list:
                return []

            # 断点续传：过滤已测试的表达式
            original_count = len(alpha_list)
            if self.resume_manager:
                alpha_list, skipped_count = self.resume_manager.filter_untested_alphas(alpha_list)

                if skipped_count > 0:
                    print(f"\n断点续传统计:")
                    print(f"   原始表达式: {original_count} 个")
                    print(f"   已测试跳过: {skipped_count} 个")
                    print(f"   待测试数量: {len(alpha_list)} 个")

                    if len(alpha_list) == 0:
                        print("所有Alpha表达式都已测试完成！")
                        return []

            print(f"\n开始模拟 {len(alpha_list)} 个 Alpha 表达式...")

            results = []
            try:
                for i, alpha in enumerate(alpha_list, 1):
                    # 显示进度（考虑跳过的数量）
                    current_index = (original_count - len(alpha_list)) + i
                    print(f"\n[{current_index}/{original_count}] 正在模拟 Alpha...")

                    result = self._simulate_single_alpha(alpha)

                    # 标记为已测试（无论成功失败）
                    if self.resume_manager:
                        expression = alpha.get('regular', '')
                        parameters = alpha.get('settings', {})
                        self.resume_manager.mark_expression_tested(
                            expression, parameters, result
                        )

                    if result and result.get('passed_all_checks'):
                        results.append(result)
                        self._save_alpha_id(result['alpha_id'], result)

                    if i < len(alpha_list):
                        sleep(5)

            except KeyboardInterrupt:
                print(f"\n用户中断，已测试 {i} 个Alpha表达式")
                if self.resume_manager:
                    self.resume_manager._signal_handler(signal.SIGINT, None)
                raise

            # 正常结束，保存断点续传状态
            if self.resume_manager:
                self.resume_manager.finalize_session()

            return results

        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"模拟过程出错: {str(e)}")
            return []

    def clear_resume_data(self):
        """清除断点续传数据"""
        if self.resume_manager:
            self.resume_manager.clear_resume_data()
            print("断点续传记录已清除，下次运行将重新开始完整测试")
        else:
            print("断点续传功能未启用")

    def get_resume_stats(self):
        """获取断点续传统计信息"""
        if self.resume_manager:
            return self.resume_manager.get_resume_stats()
        return {'total_tested': 0, 'session_tested': 0}

    def _simulate_single_alpha(self, alpha):
        """模拟单个 Alpha"""

        try:
            expression = alpha.get('regular', 'Unknown')
            settings = alpha.get('settings', {})

            print(f"表达式: {expression}")
            print(f"参数配置: Universe={settings.get('universe', 'N/A')}, "
                  f"Neutralization={settings.get('neutralization', 'N/A')}, "
                  f"Decay={settings.get('decay', 'N/A')}, "
                  f"Truncation={settings.get('truncation', 'N/A')}")

            if '_expression_type' in alpha:
                print(f"策略类型: {alpha['_expression_type']}")

            # 发送模拟请求
            simulation_url = f"{self.API_BASE_URL}/simulations"

            # 准备发送给API的数据（移除内部字段）
            api_data = {k: v for k, v in alpha.items() if not k.startswith('_')}

            print(f"模拟请求调试:")
            print(f"   URL: {simulation_url}")
            print(f"   请求方法: POST")
            print(f"   请求头: {dict(self.session.headers)}")
            print(f"   请求数据: {json.dumps(api_data, indent=2, ensure_ascii=False)}")

            sim_resp = self.session.post(simulation_url, json=api_data)

            print(f"模拟响应:")
            print(f"   状态码: {sim_resp.status_code}")
            print(f"   响应头: {dict(sim_resp.headers)}")

            if sim_resp.text:
                print(f"   响应内容: {sim_resp.text[:1000]}")

            if sim_resp.status_code != 201:
                print(f"模拟请求失败 (状态码: {sim_resp.status_code})")

                # 尝试解析错误信息
                try:
                    error_data = sim_resp.json()
                    print(f"   错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                except:
                    print(f"   原始错误: {sim_resp.text}")

                # 如果是400错误，提供详细的调试信息
                if sim_resp.status_code == 400:
                    print("\n400错误分析:")
                    print("可能的原因:")
                    print("1. 请求数据格式错误")
                    print("2. 必需字段缺失")
                    print("3. 字段值格式不正确")
                    print("4. API端点不正确")
                    print("\n建议:")
                    print("1. 检查alpha表达式语法")
                    print("2. 验证所有settings字段")
                    print("3. 确认API认证状态")

                return None

            try:
                sim_progress_url = sim_resp.headers['Location']
                start_time = datetime.now()
                total_wait = 0

                while True:
                    sim_progress_resp = self.session.get(sim_progress_url)
                    retry_after_sec = float(sim_progress_resp.headers.get("Retry-After", 0))

                    if retry_after_sec == 0:  # simulation done!
                        alpha_id = sim_progress_resp.json()['alpha']
                        print(f"获得 Alpha ID: {alpha_id}")

                        # 等待一下让指标计算完成
                        sleep(3)

                        # 获取 Alpha 详情
                        alpha_url = f"{self.API_BASE_URL}/alphas/{alpha_id}"
                        alpha_detail = self.session.get(alpha_url)
                        alpha_data = alpha_detail.json()

                        # 检查是否有 is 字段
                        if 'is' not in alpha_data:
                            print("无法获取指标数据")
                            return None

                        is_qualified = self.check_alpha_qualification(alpha_data)

                        return {
                            'expression': alpha.get('regular'),
                            'alpha_id': alpha_id,
                            'passed_all_checks': is_qualified,
                            'metrics': alpha_data.get('is', {}),
                            'parameters': alpha.get('settings', {}),
                            'expression_type': alpha.get('_expression_type', 'unknown'),
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }

                    # 更新等待时间和进度
                    total_wait += retry_after_sec
                    elapsed = (datetime.now() - start_time).total_seconds()
                    progress = min(95, (elapsed / 30) * 100)  # 假设通常需要 30 秒完成

                    print(f"等待模拟结果... ({elapsed:.1f} 秒 | 进度约 {progress:.0f}%)")
                    sleep(retry_after_sec)

            except KeyError:
                print("无法获取模拟进度 URL")
                return None

        except Exception as e:
            print(f"Alpha 模拟失败: {str(e)}")
            return None

    def check_alpha_qualification(self, alpha_data):
        """检查 Alpha 是否满足所有提交条件"""

        try:
            # 从 'is' 字段获取指标
            is_data = alpha_data.get('is', {})
            if not is_data:
                print("无法获取指标数据")
                return False

            # 获取指标值
            sharpe = float(is_data.get('sharpe', 0))
            fitness = float(is_data.get('fitness', 0))
            turnover = float(is_data.get('turnover', 0))
            ic_mean = float(is_data.get('margin', 0))  # margin 对应 IC Mean

            # 获取子宇宙 Sharpe
            sub_universe_check = next(
                (
                    check for check in is_data.get('checks', [])
                    if check['name'] == 'LOW_SUB_UNIVERSE_SHARPE'
                ),
                {}
            )
            subuniverse_sharpe = float(sub_universe_check.get('value', 0))
            required_subuniverse_sharpe = float(sub_universe_check.get('limit', 0))

            # 打印指标
            print("\nAlpha 指标详情:")
            print(f"  Sharpe: {sharpe:.3f} (>1.5)")
            print(f"  Fitness: {fitness:.3f} (>1.0)")
            print(f"  Turnover: {turnover:.3f} (0.1-0.9)")
            print(f"  IC Mean: {ic_mean:.3f} (>0.02)")
            print(f"  子宇宙 Sharpe: {subuniverse_sharpe:.3f} (>{required_subuniverse_sharpe:.3f})")

            print("\n指标评估结果:")

            # 检查每个指标并输出结果
            is_qualified = True

            if sharpe < 1.5:
                print("Sharpe ratio 不达标")
                is_qualified = False
            else:
                print("Sharpe ratio 达标")

            if fitness < 1.0:
                print("Fitness 不达标")
                is_qualified = False
            else:
                print("Fitness 达标")

            if turnover < 0.1 or turnover > 0.9:
                print("Turnover 不在合理范围")
                is_qualified = False
            else:
                print("Turnover 达标")

            if ic_mean < 0.02:
                print("IC Mean 不达标")
                is_qualified = False
            else:
                print("IC Mean 达标")

            if subuniverse_sharpe < required_subuniverse_sharpe:
                print(f"子宇宙 Sharpe 不达标 ({subuniverse_sharpe:.3f} < {required_subuniverse_sharpe:.3f})")
                is_qualified = False
            else:
                print(f"子宇宙 Sharpe 达标 ({subuniverse_sharpe:.3f} > {required_subuniverse_sharpe:.3f})")

            print("\n检查项结果:")
            checks = is_data.get('checks', [])
            for check in checks:
                name = check.get('name')
                result = check.get('result')
                value = check.get('value', 'N/A')
                limit = check.get('limit', 'N/A')

                if result == 'PASS':
                    print(f"{name}: {value} (限制: {limit}) - 通过")
                elif result == 'FAIL':
                    print(f"{name}: {value} (限制: {limit}) - 失败")
                    is_qualified = False
                elif result == 'PENDING':
                    print(f"{name}: 检查尚未完成")
                    is_qualified = False

            print("\n最终评判:")
            if is_qualified:
                print("Alpha 满足所有条件，可以提交!")
            else:
                print("Alpha 未达到提交标准")

            return is_qualified

        except Exception as e:
            print(f"检查 Alpha 资格时出错: {str(e)}")
            return False

    def submit_alpha(self, alpha_id):
        """提交单个 Alpha"""

        submit_url = f"{self.API_BASE_URL}/alphas/{alpha_id}/submit"

        for attempt in range(5):
            print(f"第 {attempt + 1} 次尝试提交 Alpha {alpha_id}")

            # POST 请求
            res = self.session.post(submit_url)
            if res.status_code == 201:
                print("POST: 成功，等待提交完成...")
            elif res.status_code in [400, 403]:
                print(f"提交被拒绝 ({res.status_code})")
                return False
            else:
                sleep(3)
                continue

            # 检查提交状态
            while True:
                res = self.session.get(submit_url)
                retry = float(res.headers.get('Retry-After', 0))

                if retry == 0:
                    if res.status_code == 200:
                        print("提交成功!")
                        return True
                    return False

                sleep(retry)

        return False

    def submit_multiple_alphas(self, alpha_ids):
        """批量提交 Alpha"""
        successful = []
        failed = []

        for alpha_id in alpha_ids:
            if self.submit_alpha(alpha_id):
                successful.append(alpha_id)
            else:
                failed.append(alpha_id)

            if alpha_id != alpha_ids[-1]:
                sleep(10)

        return successful, failed

    def _get_datafields_if_none(self, datafields=None, dataset_name=None):
        """获取数据字段列表"""

        try:
            if datafields is not None:
                return datafields

            if dataset_name is None:
                print("未指定数据集")
                return None

            config = get_dataset_config(dataset_name)
            if not config:
                print(f"无效的数据集: {dataset_name}")
                return None

            # 获取数据字段
            search_scope = {
                'instrumentType': 'EQUITY',
                'region': 'USA',
                'delay': '1',
                'universe': config['universe']
            }

            url_template = (
                f"{self.API_BASE_URL}/data-fields?"
                f"instrumentType={search_scope['instrumentType']}"
                f"&region={search_scope['region']}"
                f"&delay={search_scope['delay']}"
                f"&universe={search_scope['universe']}"
                f"&dataset.id={config['id']}"
                "&limit=50&offset={offset}"
            )

            # 获取总数
            initial_resp = self.session.get(url_template.format(offset=0))
            if initial_resp.status_code != 200:
                print("获取数据字段失败")
                return None

            total_count = initial_resp.json()['count']

            # 获取所有数据字段
            all_fields = []
            for offset in range(0, total_count, 50):
                resp = self.session.get(url_template.format(offset=offset))
                if resp.status_code != 200:
                    continue
                all_fields.extend(resp.json()['results'])

            # 过滤矩阵类型字段
            matrix_fields = [
                field['id'] for field in all_fields
                if field.get('type') == 'MATRIX'
            ]

            if not matrix_fields:
                print("未找到可用的数据字段")
                return None

            print(f"获取到 {len(matrix_fields)} 个数据字段")
            return matrix_fields

        except Exception as e:
            print(f"获取数据字段时出错: {str(e)}")
            return None

    def _generate_alpha_list(self, datafields, strategy_mode, dataset_name=None):
        """生成 Alpha 表达式列表 - 智能参数配置版本"""
        try:
            # 初始化策略生成器
            strategy_generator = AlphaStrategy()

            # 生成策略列表
            strategies = strategy_generator.get_simulation_data(datafields, strategy_mode)

            print(f"生成了 {len(strategies)} 个Alpha表达式")
            print("开始智能参数配置...")

            # 获取数据集对应的Universe参数
            dataset_universe = None
            if dataset_name:
                from dataset_config import get_dataset_config
                dataset_config = get_dataset_config(dataset_name)
                if dataset_config:
                    dataset_universe = dataset_config['universe']
                    print(f"数据集约束: Universe={dataset_universe}")

            # 转换为 API 所需的格式，使用智能参数配置
            alpha_list = []
            parameter_stats = {}

            for i, strategy in enumerate(strategies, 1):
                # 获取智能参数配置，传递数据集Universe约束
                optimal_params = self.parameter_optimizer.get_optimal_parameters(strategy, dataset_universe)

                # 统计参数使用情况
                expr_type = optimal_params['expression_type']
                parameter_stats[expr_type] = parameter_stats.get(expr_type, 0) + 1

                # 构建模拟数据 - 修复格式问题
                simulation_data = {
                    'type': 'REGULAR',
                    'settings': {
                        'instrumentType': 'EQUITY',
                        'region': 'USA',
                        'universe': optimal_params['universe'],
                        'delay': 1,
                        'decay': optimal_params['decay'],
                        'neutralization': optimal_params['neutralization'],
                        'truncation': optimal_params['truncation'],
                        'pasteurization': 'ON',
                        'unitHandling': 'VERIFY',
                        'nanHandling': 'ON',
                        'language': 'FASTEXPR',
                        'visualization': False
                    },
                    'regular': strategy
                }

                # 添加表达式类型作为额外信息（不发送给API）
                simulation_data['_expression_type'] = expr_type
                alpha_list.append(simulation_data)

                # 显示配置进度
                if i % 10 == 0 or i == len(strategies):
                    print(f"已配置 {i}/{len(strategies)} 个Alpha参数")

            # 显示参数配置统计
            print("\n智能参数配置统计:")
            for expr_type, count in parameter_stats.items():
                print(f"  {expr_type}: {count} 个Alpha")

            print(f"智能参数配置完成，共生成 {len(alpha_list)} 个优化配置")

            return alpha_list

        except Exception as e:
            print(f"生成 Alpha 列表失败: {str(e)}")
            return []

    def _save_alpha_id(self, alpha_id, result_data):
        """保存 Alpha ID 和相关信息"""
        try:
            # 保存到文件
            with open("alpha_ids.txt", "a", encoding='utf-8') as f:
                f.write(f"{alpha_id}\n")

            # 保存详细信息到JSON文件
            detailed_info = {
                'alpha_id': alpha_id,
                'expression': result_data.get('expression'),
                'timestamp': result_data.get('timestamp'),
                'metrics': result_data.get('metrics', {}),
                'parameters': result_data.get('parameters', {}),
                'expression_type': result_data.get('expression_type')
            }

            # 读取现有数据
            detailed_file = "alpha_details.json"
            if os.path.exists(detailed_file):
                with open(detailed_file, 'r', encoding='utf-8') as f:
                    all_data = json.load(f)
            else:
                all_data = []

            # 添加新数据
            all_data.append(detailed_info)

            # 保存更新后的数据
            with open(detailed_file, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)

            print(f"已保存Alpha详细信息: {alpha_id}")

        except Exception as e:
            print(f"保存Alpha信息时出错: {str(e)}")
