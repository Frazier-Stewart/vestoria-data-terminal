#!/usr/bin/env python3
"""
Test script: API endpoints

Usage:
    # Start the server first:
    uvicorn app.main:app --port 8000
    
    # Then run tests:
    python tests/test_api.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"


def test_api_root():
    """测试 API 根路径"""
    print("=" * 50)
    print("Test 1: API Root")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            print(f"✅ API root OK: {response.json()}")
            return True
        else:
            print(f"❌ API root failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        print("   Make sure server is running: uvicorn app.main:app --port 8000")
        return False


def test_get_assets():
    """测试获取资产列表"""
    print("\n" + "=" * 50)
    print("Test 2: GET /assets")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/assets")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {len(data)} assets:")
            for asset in data[:5]:  # Show first 5
                print(f"   - {asset['id']}: {asset['name']}")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_get_prices():
    """测试获取价格数据"""
    print("\n" + "=" * 50)
    print("Test 3: GET /prices/{asset_id}")
    print("=" * 50)
    
    asset_ids = ['BTC-USD', 'SPY']
    
    for asset_id in asset_ids:
        try:
            response = requests.get(f"{BASE_URL}/prices/{asset_id}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {asset_id}: {len(data)} price records")
                if data:
                    print(f"   Latest: {data[-1]['date']} @ {data[-1]['close']}")
            else:
                print(f"⚠️  {asset_id}: {response.status_code}")
        except Exception as e:
            print(f"❌ {asset_id}: {e}")
    
    return True


def test_get_indicator_templates():
    """测试获取指标模板"""
    print("\n" + "=" * 50)
    print("Test 4: GET /indicators/templates")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/indicators/templates")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {len(data)} templates:")
            for t in data:
                print(f"   - {t['id']}: {t['name']} ({t['category']})")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_get_indicators():
    """测试获取指标实例"""
    print("\n" + "=" * 50)
    print("Test 5: GET /indicators")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/indicators")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {len(data)} indicators:")
            for i in data:
                print(f"   - {i['name']} ({i['template_id']})")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_get_indicator_values():
    """测试获取指标数值"""
    print("\n" + "=" * 50)
    print("Test 6: GET /indicators/{id}/values")
    print("=" * 50)
    
    try:
        # First get indicator list
        response = requests.get(f"{BASE_URL}/indicators")
        if response.status_code != 200:
            print("❌ Failed to get indicators list")
            return False
        
        indicators = response.json()
        
        for indicator in indicators[:2]:  # Test first 2
            ind_id = indicator['id']
            try:
                response = requests.get(f"{BASE_URL}/indicators/{ind_id}/values")
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ {indicator['name']}: {len(data)} values")
                    if data:
                        latest = data[-1]
                        print(f"   Latest: {latest['date']} = {latest['value']:.2f}")
                else:
                    print(f"⚠️  {indicator['name']}: {response.status_code}")
            except Exception as e:
                print(f"❌ {indicator['name']}: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_get_indicator_latest():
    """测试获取最新指标值"""
    print("\n" + "=" * 50)
    print("Test 7: GET /indicators/{id}/latest")
    print("=" * 50)
    
    try:
        # Get indicator list
        response = requests.get(f"{BASE_URL}/indicators")
        if response.status_code != 200:
            print("❌ Failed to get indicators list")
            return False
        
        indicators = response.json()
        
        for indicator in indicators[:2]:
            ind_id = indicator['id']
            try:
                response = requests.get(f"{BASE_URL}/indicators/{ind_id}/latest")
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ {indicator['name']}:")
                    print(f"   Value: {data.get('value')}")
                    print(f"   Grade: {data.get('grade_label')}")
                else:
                    print(f"⚠️  {indicator['name']}: {response.status_code}")
            except Exception as e:
                print(f"❌ {indicator['name']}: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_docs():
    """测试 API 文档"""
    print("\n" + "=" * 50)
    print("Test 8: API Docs")
    print("=" * 50)
    
    urls = [
        "http://localhost:8000/docs",
        "http://localhost:8000/openapi.json"
    ]
    
    for url in urls:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print(f"✅ {url} - OK")
            else:
                print(f"⚠️  {url} - {response.status_code}")
        except Exception as e:
            print(f"❌ {url} - {e}")
    
    return True


if __name__ == "__main__":
    print("\n" + "🌐" * 25)
    print("Data Terminal - API Tests")
    print("🌐" * 25)
    print("\n⚠️  Make sure server is running:")
    print("   uvicorn app.main:app --port 8000\n")
    
    tests = [
        ("API Root", test_api_root),
        ("Get Assets", test_get_assets),
        ("Get Prices", test_get_prices),
        ("Indicator Templates", test_get_indicator_templates),
        ("Get Indicators", test_get_indicators),
        ("Indicator Values", test_get_indicator_values),
        ("Indicator Latest", test_get_indicator_latest),
        ("API Docs", test_docs),
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
        print("🎉 All API tests passed!")
    else:
        print("⚠️  Some tests failed")
