"""WorldQuant Brain API 批量处理模块"""

import requests
import json
import pandas as pd
from os.path import expanduser
from requests.auth import HTTPBasicAuth
from time import sleep
from datetime import datetime
import os
from dataset_config import get_dataset_config, get_api_settings
from alpha_strategy import AlphaStrategy

class BrainBatchAlpha:
    API_BASE_URL = 'https://api.worldquantbrain.com'
    
    def __init__(self, credentials_file='brain_credentials.txt'):
        """初始化API客户端"""
        self.sess = requests.Session()
        self._setup_authentication(credentials_file)
        
    def _setup_authentication(self, credentials_file):
        """设置认证"""
        try:
            with open(expanduser(credentials_file)) as f:
                credentials = json.load(f)
            username, password = credentials
            self.sess.auth = HTTPBasicAuth(username, password)
            
            response = self.sess.post(f"{self.API_BASE_URL}/authentication")
            if response.status_code not in [200, 201]:
                raise Exception(f"认证失败: HTTP {response.status_code}")
                
            print("✅ 认证成功!")
            
        except Exception as e:
            print(f"❌ 认证错误: {str(e)}")
            raise
            
    def simulate_alphas(self, datafields=None, strategy_mode=1, dataset_name=None):
        """模拟Alpha列表"""
        try:
            datafields = self._get_datafields_if_none(datafields, dataset_name)
            if not datafields:
                return []
                
            alpha_list = self._generate_alpha_list(datafields, strategy_mode)
            if not alpha_list:
                return []
                
            print(f"\n🚀 开始模拟 {len(alpha_list)} 个Alpha表达式...")
            
            results = []
            for i, alpha in enumerate(alpha_list, 1):
                print(f"\n[{i}/{len(alpha_list)}] 正在模拟Alpha...")
                result = self._simulate_single_alpha(alpha)
                if result and result.get('passed_all_checks'):
                    results.append(result)
                    self._save_alpha_id(result['alpha_id'], result)
                
                if i < len(alpha_list):
                    sleep(5)
                    
            return results
            
        except Exception as e:
            print(f"❌ 模拟过程出错: {str(e)}")
            return []
            
    def _simulate_single_alpha(self, alpha):
        """模拟单个Alpha"""
        try:
            print(f"表达式: {alpha.get('regular', 'Unknown')}")
            
            # 发送模拟请求
            sim_resp = self.sess.post(
                f"{self.API_BASE_URL}/simulations",
                json=alpha
            )
            
            if sim_resp.status_code != 201:
                print(f"❌ 模拟请求失败 (状态码: {sim_resp.status_code})")
                return None
                
            try:
                sim_progress_url = sim_resp.headers['Location']
                start_time = datetime.now()
                total_wait = 0
                
                while True:
                    sim_progress_resp = self.sess.get(sim_progress_url)
                    retry_after_sec = float(sim_progress_resp.headers.get("Retry-After", 0))
                    
                    if retry_after_sec == 0:  # simulation done!
                        alpha_id = sim_progress_resp.json()['alpha']
                        print(f"✅ 获得Alpha ID: {alpha_id}")
                        
                        # 等待一下让指标计算完成
                        sleep(3)
                        
                        # 获取Alpha详情
                        alpha_url = f"{self.API_BASE_URL}/alphas/{alpha_id}"
                        alpha_detail = self.sess.get(alpha_url)
                        alpha_data = alpha_detail.json()
                        
                        # 检查是否有is字段
                        if 'is' not in alpha_data:
                            print("❌ 无法获取指标数据")
                            return None
                            
                        is_qualified = self.check_alpha_qualification(alpha_data)
                        
                        return {
                            'expression': alpha.get('regular'),
                            'alpha_id': alpha_id,
                            'passed_all_checks': is_qualified,
                            'metrics': alpha_data.get('is', {}),
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                    # 更新等待时间和进度
                    total_wait += retry_after_sec
                    elapsed = (datetime.now() - start_time).total_seconds()
                    progress = min(95, (elapsed / 30) * 100)  # 假设通常需要30秒完成
                    
                    print(f"⏳ 等待模拟结果... ({elapsed:.1f}秒 | 进度约 {progress:.0f}%)")
                    sleep(retry_after_sec)
                    
            except KeyError:
                print("❌ 无法获取模拟进度URL")
                return None
                
        except Exception as e:
            print(f"⚠️ Alpha模拟失败: {str(e)}")
            return None
            
    def check_alpha_qualification(self, alpha_data):
        """检查Alpha是否满足所有提交条件"""
        try:
            # 从 'is' 字段获取指标
            is_data = alpha_data.get('is', {})
            if not is_data:
                print("❌ 无法获取指标数据")
                return False
            
            # 获取指标值
            sharpe = float(is_data.get('sharpe', 0))
            fitness = float(is_data.get('fitness', 0))
            turnover = float(is_data.get('turnover', 0))
            ic_mean = float(is_data.get('margin', 0))  # margin 对应 IC Mean
            
            # 获取子宇宙Sharpe
            sub_universe_check = next(
                (check for check in is_data.get('checks', [])
                 if check['name'] == 'LOW_SUB_UNIVERSE_SHARPE'),
                {}
            )
            subuniverse_sharpe = float(sub_universe_check.get('value', 0))
            required_subuniverse_sharpe = float(sub_universe_check.get('limit', 0))
            
            # 打印指标
            print("\n📊 Alpha指标详情:")
            print(f"  Sharpe: {sharpe:.3f} (>1.5)")
            print(f"  Fitness: {fitness:.3f} (>1.0)")
            print(f"  Turnover: {turnover:.3f} (0.1-0.9)")
            print(f"  IC Mean: {ic_mean:.3f} (>0.02)")
            print(f"  子宇宙Sharpe: {subuniverse_sharpe:.3f} (>{required_subuniverse_sharpe:.3f})")
            
            print("\n📝 指标评估结果:")
            
            # 检查每个指标并输出结果
            is_qualified = True
            
            if sharpe < 1.5:
                print("❌ Sharpe ratio 不达标")
                is_qualified = False
            else:
                print("✅ Sharpe ratio 达标")
            
            if fitness < 1.0:
                print("❌ Fitness 不达标")
                is_qualified = False
            else:
                print("✅ Fitness 达标")
            
            if turnover < 0.1 or turnover > 0.9:
                print("❌ Turnover 不在合理范围")
                is_qualified = False
            else:
                print("✅ Turnover 达标")
            
            if ic_mean < 0.02:
                print("❌ IC Mean 不达标")
                is_qualified = False
            else:
                print("✅ IC Mean 达标")
            
            if subuniverse_sharpe < required_subuniverse_sharpe:
                print(f"❌ 子宇宙Sharpe不达标 ({subuniverse_sharpe:.3f} < {required_subuniverse_sharpe:.3f})")
                is_qualified = False
            else:
                print(f"✅ 子宇宙Sharpe达标 ({subuniverse_sharpe:.3f} > {required_subuniverse_sharpe:.3f})")
            
            print("\n🔍 检查项结果:")
            checks = is_data.get('checks', [])
            for check in checks:
                name = check.get('name')
                result = check.get('result')
                value = check.get('value', 'N/A')
                limit = check.get('limit', 'N/A')
                
                if result == 'PASS':
                    print(f"✅ {name}: {value} (限制: {limit})")
                elif result == 'FAIL':
                    print(f"❌ {name}: {value} (限制: {limit})")
                    is_qualified = False
                elif result == 'PENDING':
                    print(f"⚠️ {name}: 检查尚未完成")
                    is_qualified = False
            
            print("\n📋 最终评判:")
            if is_qualified:
                print("✅ Alpha 满足所有条件，可以提交!")
            else:
                print("❌ Alpha 未达到提交标准")
            
            return is_qualified
            
        except Exception as e:
            print(f"❌ 检查Alpha资格时出错: {str(e)}")
            return False
            
    def submit_alpha(self, alpha_id):
        """提交单个Alpha"""
        submit_url = f"{self.API_BASE_URL}/alphas/{alpha_id}/submit"
        
        for attempt in range(5):
            print(f"🔄 第 {attempt + 1} 次尝试提交 Alpha {alpha_id}")
            
            # POST请求
            res = self.sess.post(submit_url)
            if res.status_code == 201:
                print("✅ POST成功，等待提交完成...")
            elif res.status_code in [400, 403]:
                print(f"❌ 提交被拒绝 ({res.status_code})")
                return False
            else:
                sleep(3)
                continue
                
            # 检查提交状态
            while True:
                res = self.sess.get(submit_url)
                retry = float(res.headers.get('Retry-After', 0))
                
                if retry == 0:
                    if res.status_code == 200:
                        print("✅ 提交成功!")
                        return True
                    return False
                    
                sleep(retry)
                
        return False
        
    def submit_multiple_alphas(self, alpha_ids):
        """批量提交Alpha"""
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
                print("❌ 未指定数据集")
                return None
            
            config = get_dataset_config(dataset_name)
            if not config:
                print(f"❌ 无效的数据集: {dataset_name}")
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
            initial_resp = self.sess.get(url_template.format(offset=0))
            if initial_resp.status_code != 200:
                print("❌ 获取数据字段失败")
                return None
            
            total_count = initial_resp.json()['count']
            
            # 获取所有数据字段
            all_fields = []
            for offset in range(0, total_count, 50):
                resp = self.sess.get(url_template.format(offset=offset))
                if resp.status_code != 200:
                    continue
                all_fields.extend(resp.json()['results'])
            
            # 过滤矩阵类型字段
            matrix_fields = [
                field['id'] for field in all_fields 
                if field.get('type') == 'MATRIX'
            ]
            
            if not matrix_fields:
                print("❌ 未找到可用的数据字段")
                return None
            
            print(f"✅ 获取到 {len(matrix_fields)} 个数据字段")
            return matrix_fields
            
        except Exception as e:
            print(f"❌ 获取数据字段时出错: {str(e)}")
            return None
        
    def _generate_alpha_list(self, datafields, strategy_mode):
        """生成Alpha表达式列表"""
        try:
            # 初始化策略生成器
            strategy_generator = AlphaStrategy()
            
            # 生成策略列表
            strategies = strategy_generator.get_simulation_data(datafields, strategy_mode)
            
            print(f"生成了 {len(strategies)} 个Alpha表达式")
            
            # 转换为API所需的格式
            alpha_list = []
            for strategy in strategies:
                simulation_data = {
                    'type': 'REGULAR',
                    'settings': {
                        'instrumentType': 'EQUITY',
                        'region': 'USA',
                        'universe': 'TOP3000',
                        'delay': 1,
                        'decay': 0,
                        'neutralization': 'SUBINDUSTRY',
                        'truncation': 0.08,
                        'pasteurization': 'ON',
                        'unitHandling': 'VERIFY',
                        'nanHandling': 'ON',
                        'language': 'FASTEXPR',
                        'visualization': False,
                    },
                    'regular': strategy
                }
                alpha_list.append(simulation_data)
                
            return alpha_list
            
        except Exception as e:
            print(f"❌ 生成Alpha列表失败: {str(e)}")
            return []