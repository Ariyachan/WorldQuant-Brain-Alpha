"""智能参数配置效果分析工具"""

import json
import os
from collections import defaultdict


class ParameterAnalyzer:
    """参数配置效果分析器"""
    
    def __init__(self, details_file="alpha_details.json"):
        """初始化分析器"""
        self.details_file = details_file
        self.data = self._load_data()
    
    def _load_data(self):
        """加载Alpha详细数据"""
        if not os.path.exists(self.details_file):
            print(f"❌ 数据文件不存在: {self.details_file}")
            return []
        
        try:
            with open(self.details_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 加载数据失败: {str(e)}")
            return []
    
    def analyze_parameter_performance(self):
        """分析参数配置性能"""
        if not self.data:
            print("❌ 没有可分析的数据")
            return
        
        print("📊 智能参数配置效果分析报告")
        print("=" * 50)
        
        # 按表达式类型分组分析
        type_stats = defaultdict(list)
        for alpha in self.data:
            expr_type = alpha.get('expression_type', 'unknown')
            metrics = alpha.get('metrics', {})
            parameters = alpha.get('parameters', {})
            
            type_stats[expr_type].append({
                'sharpe': float(metrics.get('sharpe', 0)),
                'fitness': float(metrics.get('fitness', 0)),
                'turnover': float(metrics.get('turnover', 0)),
                'ic_mean': float(metrics.get('margin', 0)),
                'universe': parameters.get('universe'),
                'neutralization': parameters.get('neutralization'),
                'decay': parameters.get('decay'),
                'truncation': parameters.get('truncation')
            })
        
        # 输出分析结果
        for expr_type, alphas in type_stats.items():
            print(f"\n🎯 {expr_type.upper()} 策略分析 ({len(alphas)} 个Alpha)")
            print("-" * 30)
            
            if alphas:
                avg_sharpe = sum(a['sharpe'] for a in alphas) / len(alphas)
                avg_fitness = sum(a['fitness'] for a in alphas) / len(alphas)
                avg_turnover = sum(a['turnover'] for a in alphas) / len(alphas)
                avg_ic_mean = sum(a['ic_mean'] for a in alphas) / len(alphas)
                
                print(f"  平均 Sharpe: {avg_sharpe:.3f}")
                print(f"  平均 Fitness: {avg_fitness:.3f}")
                print(f"  平均 Turnover: {avg_turnover:.3f}")
                print(f"  平均 IC Mean: {avg_ic_mean:.3f}")
                
                # 参数使用统计
                universe_count = defaultdict(int)
                neutralization_count = defaultdict(int)
                
                for alpha in alphas:
                    universe_count[alpha['universe']] += 1
                    neutralization_count[alpha['neutralization']] += 1
                
                print(f"  常用Universe: {dict(universe_count)}")
                print(f"  常用Neutralization: {dict(neutralization_count)}")
    
    def analyze_best_parameters(self):
        """分析最佳参数组合"""
        if not self.data:
            return
        
        print("\n🏆 最佳参数组合分析")
        print("=" * 50)
        
        # 找出高性能Alpha
        high_performance_alphas = []
        for alpha in self.data:
            metrics = alpha.get('metrics', {})
            sharpe = float(metrics.get('sharpe', 0))
            fitness = float(metrics.get('fitness', 0))
            
            if sharpe >= 1.5 and fitness >= 1.0:
                high_performance_alphas.append(alpha)
        
        if not high_performance_alphas:
            print("❌ 没有找到高性能Alpha")
            return
        
        print(f"✅ 找到 {len(high_performance_alphas)} 个高性能Alpha")
        
        # 分析高性能Alpha的参数特征
        param_combinations = defaultdict(int)
        for alpha in high_performance_alphas:
            params = alpha.get('parameters', {})
            combination = f"{params.get('universe')}-{params.get('neutralization')}-{params.get('decay')}"
            param_combinations[combination] += 1
        
        print("\n🎯 高性能参数组合排行:")
        sorted_combinations = sorted(param_combinations.items(), key=lambda x: x[1], reverse=True)
        for i, (combination, count) in enumerate(sorted_combinations[:5], 1):
            print(f"  {i}. {combination}: {count} 次")
    
    def generate_optimization_suggestions(self):
        """生成参数优化建议"""
        if not self.data:
            return
        
        print("\n💡 参数优化建议")
        print("=" * 50)
        
        # 分析各参数对性能的影响
        universe_performance = defaultdict(list)
        neutralization_performance = defaultdict(list)
        
        for alpha in self.data:
            metrics = alpha.get('metrics', {})
            parameters = alpha.get('parameters', {})
            
            sharpe = float(metrics.get('sharpe', 0))
            fitness = float(metrics.get('fitness', 0))
            performance_score = (sharpe + fitness) / 2
            
            universe_performance[parameters.get('universe')].append(performance_score)
            neutralization_performance[parameters.get('neutralization')].append(performance_score)
        
        # Universe建议
        print("🌍 Universe参数建议:")
        for universe, scores in universe_performance.items():
            avg_score = sum(scores) / len(scores) if scores else 0
            print(f"  {universe}: 平均性能 {avg_score:.3f} ({len(scores)} 个样本)")
        
        # Neutralization建议
        print("\n⚖️ Neutralization参数建议:")
        for neutralization, scores in neutralization_performance.items():
            avg_score = sum(scores) / len(scores) if scores else 0
            print(f"  {neutralization}: 平均性能 {avg_score:.3f} ({len(scores)} 个样本)")


def main():
    """主函数"""
    analyzer = ParameterAnalyzer()
    
    if analyzer.data:
        analyzer.analyze_parameter_performance()
        analyzer.analyze_best_parameters()
        analyzer.generate_optimization_suggestions()
    else:
        print("❌ 没有可分析的数据，请先运行Alpha模拟生成数据")


if __name__ == "__main__":
    main()
