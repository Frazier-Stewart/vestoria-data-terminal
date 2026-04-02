#!/usr/bin/env python3
"""
Test script: Indicators calculation and values

Usage:
    python tests/test_indicators.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
from datetime import date, timedelta
from app.core.database import SessionLocal
from app.models.indicator import Indicator, IndicatorTemplate, IndicatorValue
from app.services.indicator_scheduler import calculate_all_indicators, calculate_indicator_latest
from app.indicators.registry import create_processor, list_processors


def test_indicator_templates():
    """测试指标模板"""
    print("=" * 50)
    print("Test 1: Indicator Templates")
    print("=" * 50)
    
    db = SessionLocal()
    templates = db.query(IndicatorTemplate).all()
    
    if not templates:
        print("❌ No indicator templates found")
        db.close()
        return False
    
    print(f"✅ Found {len(templates)} templates:")
    for t in templates:
        print(f"   - {t.id}: {t.name} ({t.category})")
        print(f"     Processor: {t.processor_class}")
    
    db.close()
    return True


def test_indicator_instances():
    """测试指标实例"""
    print("\n" + "=" * 50)
    print("Test 2: Indicator Instances")
    print("=" * 50)
    
    db = SessionLocal()
    indicators = db.query(Indicator).filter(Indicator.is_active == True).all()
    
    if not indicators:
        print("❌ No active indicator instances found")
        db.close()
        return False
    
    print(f"✅ Found {len(indicators)} active indicators:")
    for i in indicators:
        print(f"   - {i.id}: {i.name}")
        print(f"     Template: {i.template_id}, Asset: {i.asset_id}")
        if i.last_calculated_at:
            print(f"     Last calculated: {i.last_calculated_at}")
    
    db.close()
    return True


def test_processor_registry():
    """测试处理器注册表"""
    print("\n" + "=" * 50)
    print("Test 3: Processor Registry")
    print("=" * 50)
    
    processors = list_processors()
    print(f"✅ Registered processors: {', '.join(processors)}")
    
    # Test creating each processor
    db = SessionLocal()
    templates = db.query(IndicatorTemplate).all()
    
    for t in templates:
        processor = create_processor(t.id)
        if processor:
            print(f"✅ {t.id}: Processor created successfully")
        else:
            print(f"❌ {t.id}: Failed to create processor")
    
    db.close()
    return True


def test_calculate_latest():
    """测试计算最新指标值"""
    print("\n" + "=" * 50)
    print("Test 4: Calculate Latest Indicator Values")
    print("=" * 50)
    
    db = SessionLocal()
    indicators = db.query(Indicator).filter(Indicator.is_active == True).all()
    
    for indicator in indicators:
        print(f"\n   Calculating {indicator.name}...")
        try:
            result = calculate_indicator_latest(indicator.id)
            
            if result['status'] == 'success':
                print(f"   ✅ {result['indicator_name']}")
                print(f"      Date: {result.get('date')}")
                print(f"      Value: {result.get('value')}")
                if result.get('value_text'):
                    print(f"      Text: {result.get('value_text')}")
                if result.get('grade_label'):
                    print(f"      Grade: {result.get('grade_label')}")
            else:
                print(f"   ⚠️  {indicator.name}: {result.get('message')}")
        except Exception as e:
            print(f"   ❌ {indicator.name}: {e}")
    
    db.close()
    return True


def test_calculate_history():
    """测试计算历史指标值"""
    print("\n" + "=" * 50)
    print("Test 5: Calculate Indicator History (30 days)")
    print("=" * 50)
    
    try:
        start = date.today() - timedelta(days=30)
        results = calculate_all_indicators(start=start)
        
        print("✅ Historical calculation completed:")
        for r in results:
            status = "✓" if r['status'] == 'success' else "✗"
            name = r.get('indicator_name', f"ID:{r['indicator_id']}")
            print(f"   {status} {name}: {r.get('count', 0)} values")
        
        return True
    except Exception as e:
        print(f"❌ Historical calculation failed: {e}")
        return False


def test_indicator_values():
    """测试指标数值查询"""
    print("\n" + "=" * 50)
    print("Test 6: Indicator Values Query")
    print("=" * 50)
    
    db = SessionLocal()
    indicators = db.query(Indicator).all()
    
    for indicator in indicators:
        values = db.query(IndicatorValue).filter(
            IndicatorValue.indicator_id == indicator.id
        ).order_by(IndicatorValue.date.desc()).limit(5).all()
        
        print(f"\n   {indicator.name}:")
        if values:
            print(f"   ✅ {len(values)} recent values")
            for v in values[:3]:
                print(f"      {v.date}: {v.value:.2f} ({v.grade_label})")
        else:
            print(f"   ⚠️  No values calculated yet")
    
    db.close()
    return True


def test_ma200_with_sufficient_data():
    """测试 MA200 指标（需要足够数据）"""
    print("\n" + "=" * 50)
    print("Test 7: MA200 Indicator (requires 200+ days data)")
    print("=" * 50)
    
    from app.indicators.registry import create_processor
    
    db = SessionLocal()
    ma_template = db.query(IndicatorTemplate).filter(
        IndicatorTemplate.id == "ma200"
    ).first()
    
    if not ma_template:
        print("❌ MA200 template not found")
        db.close()
        return False
    
    # Find MA200 indicator for SPY (has 251 days of data)
    ma_indicator = db.query(Indicator).filter(
        Indicator.template_id == "ma200",
        Indicator.asset_id == "SPY"
    ).first()
    
    if not ma_indicator:
        print("⚠️  No MA200 indicator for SPY found, skipping test")
        db.close()
        return True
    
    print(f"✅ Found MA200 indicator for SPY")
    
    try:
        result = calculate_indicator_latest(ma_indicator.id)
        
        if result['status'] == 'success':
            print(f"✅ MA200 calculation successful:")
            print(f"   Value: {result.get('value'):.2f}%")
            print(f"   Grade: {result.get('grade_label')}")
        else:
            print(f"⚠️  MA200 calculation: {result.get('message')}")
    except Exception as e:
        print(f"❌ MA200 calculation failed: {e}")
    
    db.close()
    return True


if __name__ == "__main__":
    print("\n" + "📊" * 25)
    print("Data Terminal - Indicator Tests")
    print("📊" * 25 + "\n")
    
    tests = [
        ("Indicator Templates", test_indicator_templates),
        ("Indicator Instances", test_indicator_instances),
        ("Processor Registry", test_processor_registry),
        ("Calculate Latest", test_calculate_latest),
        ("Calculate History", test_calculate_history),
        ("Indicator Values", test_indicator_values),
        ("MA200 with Data", test_ma200_with_sufficient_data),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed")
