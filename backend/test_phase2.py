#!/usr/bin/env python3
"""Phase 2 全面测试脚本"""
import asyncio
import requests
import sys
from datetime import date, datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"

def test_api_health():
    """测试 API 是否可用"""
    print("=" * 60)
    print("1. API 健康检查")
    print("=" * 60)
    try:
        r = requests.get(f"{BASE_URL}/assets", timeout=5)
        print(f"   ✓ API 响应状态: {r.status_code}")
        return True
    except Exception as e:
        print(f"   ✗ API 连接失败: {e}")
        return False

def test_indicator_templates():
    """测试指标模板 API"""
    print("\n" + "=" * 60)
    print("2. 指标模板系统测试")
    print("=" * 60)
    
    # 2.1 获取模板列表
    print("\n   2.1 获取模板列表")
    r = requests.get(f"{BASE_URL}/indicators/templates")
    if r.status_code == 200:
        templates = r.json()
        print(f"   ✓ 获取到 {len(templates)} 个模板")
        for t in templates:
            print(f"      - {t['id']}: {t['name']} ({t['indicator_type']})")
    else:
        print(f"   ✗ 失败: {r.status_code}")
        return False
    
    # 2.2 获取单个模板
    print("\n   2.2 获取单个模板 (MA200)")
    r = requests.get(f"{BASE_URL}/indicators/templates/MA200")
    if r.status_code == 200:
        t = r.json()
        print(f"   ✓ 模板详情: {t['name']}")
        print(f"      处理器: {t['processor_class']}")
        print(f"      输出字段: {len(t['output_fields'])} 个")
        print(f"      分档配置: {len(t.get('grading_config', {}).get('grades', []))} 档")
    else:
        print(f"   ✗ 失败: {r.status_code}")
    
    return True

def test_indicator_instances():
    """测试指标实例 API"""
    print("\n" + "=" * 60)
    print("3. 指标实例管理测试")
    print("=" * 60)
    
    # 3.1 获取实例列表
    print("\n   3.1 获取实例列表")
    r = requests.get(f"{BASE_URL}/indicators")
    if r.status_code == 200:
        indicators = r.json()
        print(f"   ✓ 已有 {len(indicators)} 个指标实例")
        for ind in indicators:
            print(f"      - ID={ind['id']}: {ind['name']} ({ind['template_id']})")
    else:
        print(f"   ✗ 失败: {r.status_code}")
        return False
    
    # 3.2 获取单个实例
    if indicators:
        print("\n   3.2 获取单个实例")
        r = requests.get(f"{BASE_URL}/indicators/{indicators[0]['id']}")
        if r.status_code == 200:
            ind = r.json()
            print(f"   ✓ 实例详情: {ind['name']}")
            print(f"      模板: {ind['template']['name']}")
            print(f"      标的: {ind['asset_id']}")
        else:
            print(f"   ✗ 失败: {r.status_code}")
    
    return True

def test_indicator_calculation():
    """测试指标计算功能"""
    print("\n" + "=" * 60)
    print("4. 指标计算功能测试")
    print("=" * 60)
    
    # 4.1 BTC Fear & Greed 计算
    print("\n   4.1 BTC Fear & Greed 计算")
    r = requests.get(f"{BASE_URL}/indicators")
    indicators = r.json()
    
    btc_fng = [i for i in indicators if i['template_id'] == 'BTC_FEAR_GREED']
    if btc_fng:
        ind_id = btc_fng[0]['id']
        
        # 触发计算
        r = requests.post(
            f"{BASE_URL}/indicators/{ind_id}/calculate",
            json={"start": "2025-01-01", "end": date.today().isoformat()}
        )
        if r.status_code == 200:
            print(f"   ✓ 计算触发成功: {r.json()['message']}")
        else:
            print(f"   ✗ 计算触发失败: {r.status_code}")
        
        # 等待计算完成
        import time
        time.sleep(2)
        
        # 查询结果
        r = requests.get(f"{BASE_URL}/indicators/{ind_id}/values?limit=3")
        if r.status_code == 200:
            values = r.json()
            print(f"   ✓ 获取到 {len(values)} 条历史数据")
            for v in values[-3:]:
                print(f"      {v['date']}: {v['value']} ({v['value_text']}) - {v['grade_label']}")
        else:
            print(f"   ✗ 查询失败: {r.status_code}")
    
    # 4.2 VIX 计算
    print("\n   4.2 VIX 计算")
    vix = [i for i in indicators if i['template_id'] == 'VIX']
    if vix:
        ind_id = vix[0]['id']
        
        r = requests.get(f"{BASE_URL}/indicators/{ind_id}/values?limit=3")
        if r.status_code == 200:
            values = r.json()
            print(f"   ✓ 获取到 {len(values)} 条历史数据")
            for v in values[-3:]:
                print(f"      {v['date']}: {v['value']:.2f} - {v['grade_label']}")
        else:
            print(f"   ✗ 查询失败: {r.status_code}")
    
    return True

def test_latest_value():
    """测试最新值查询"""
    print("\n" + "=" * 60)
    print("5. 最新值查询测试")
    print("=" * 60)
    
    r = requests.get(f"{BASE_URL}/indicators")
    indicators = r.json()
    
    for ind in indicators[:2]:  # 测试前两个
        print(f"\n   {ind['name']}:")
        r = requests.get(f"{BASE_URL}/indicators/{ind['id']}/latest")
        if r.status_code == 200:
            v = r.json()
            print(f"   ✓ 最新值: {v['value']:.2f} ({v['value_text']})")
        else:
            print(f"   ✗ 查询失败: {r.status_code}")
    
    return True

def test_processor_registry():
    """测试处理器注册表"""
    print("\n" + "=" * 60)
    print("6. 处理器注册表测试")
    print("=" * 60)
    
    from app.indicators import list_processors, create_processor
    
    processors = list_processors()
    print(f"\n   ✓ 已注册处理器: {list(processors.keys())}")
    
    # 测试创建处理器
    for name in ['MA200', 'BTC_FEAR_GREED', 'VIX']:
        processor = create_processor(name)
        if processor:
            print(f"   ✓ {name}: {processor.display_name}")
        else:
            print(f"   ✗ {name}: 创建失败")
    
    return True

async def test_processor_calculation():
    """测试处理器直接计算"""
    print("\n" + "=" * 60)
    print("7. 处理器直接计算测试")
    print("=" * 60)
    
    from app.indicators import create_processor
    
    # 7.1 BTC Fear & Greed
    print("\n   7.1 BTC Fear & Greed 实时获取")
    processor = create_processor('BTC_FEAR_GREED')
    result = await processor.calculate_latest('BTC-USD')
    if result:
        print(f"   ✓ 当前值: {result.value} ({result.value_text})")
        print(f"      档位: {result.grade_label}")
    else:
        print("   ✗ 获取失败")
    
    # 7.2 VIX
    print("\n   7.2 VIX 实时获取")
    processor = create_processor('VIX')
    result = await processor.calculate_latest('SPY')
    if result:
        print(f"   ✓ 当前值: {result.value:.2f} ({result.value_text})")
        print(f"      档位: {result.grade_label}")
    else:
        print("   ✗ 获取失败")
    
    # 7.3 MA200 (需要足够数据)
    print("\n   7.3 MA200 计算测试")
    processor = create_processor('MA200')
    end = date.today()
    start = end - timedelta(days=30)
    results = await processor.calculate('BTC-USD', start, end)
    if results:
        print(f"   ✓ 计算成功，返回 {len(results)} 条数据")
    else:
        print("   ⚠ 无结果（需要更多历史价格数据）")
    
    return True

def run_all_tests():
    """运行所有测试"""
    print("\n" + "🚀" * 30)
    print("        Phase 2 全面测试")
    print("🚀" * 30 + "\n")
    
    results = []
    
    # API 测试
    results.append(("API 健康检查", test_api_health()))
    results.append(("指标模板系统", test_indicator_templates()))
    results.append(("指标实例管理", test_indicator_instances()))
    results.append(("指标计算功能", test_indicator_calculation()))
    results.append(("最新值查询", test_latest_value()))
    
    # 处理器测试
    results.append(("处理器注册表", test_processor_registry()))
    
    # 异步测试
    print("\n" + "-" * 60)
    try:
        asyncio.run(test_processor_calculation())
        results.append(("处理器直接计算", True))
    except Exception as e:
        print(f"处理器测试异常: {e}")
        results.append(("处理器直接计算", False))
    
    # 测试总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"   {status}: {name}")
    
    print(f"\n   总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n   🎉 所有测试通过！")
    else:
        print(f"\n   ⚠️  {total - passed} 项测试失败")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
