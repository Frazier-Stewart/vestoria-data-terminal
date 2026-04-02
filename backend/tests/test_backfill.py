#!/usr/bin/env python3
"""
Test script: Backfill and price data verification

Usage:
    python tests/test_backfill.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import date, timedelta
from app.core.database import SessionLocal
from app.models.asset import Asset
from app.models.price_data import PriceData
from app.services.backfill import backfill_all_assets, incremental_update
from sqlalchemy import func


def test_database_connection():
    """测试数据库连接"""
    print("=" * 50)
    print("Test 1: Database Connection")
    print("=" * 50)
    
    try:
        db = SessionLocal()
        result = db.execute("SELECT 1").scalar()
        print(f"✅ Database connection OK: {result}")
        db.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def test_assets_exist():
    """测试资产是否存在"""
    print("\n" + "=" * 50)
    print("Test 2: Assets Exist")
    print("=" * 50)
    
    db = SessionLocal()
    assets = db.query(Asset).all()
    
    if not assets:
        print("❌ No assets found in database")
        db.close()
        return False
    
    print(f"✅ Found {len(assets)} assets:")
    for asset in assets:
        print(f"   - {asset.id} ({asset.symbol}): {asset.name}")
    
    db.close()
    return True


def test_price_data():
    """测试价格数据"""
    print("\n" + "=" * 50)
    print("Test 3: Price Data")
    print("=" * 50)
    
    db = SessionLocal()
    
    for asset_id in ['BTC-USD', 'SPY']:
        count = db.query(func.count(PriceData.id)).filter(
            PriceData.asset_id == asset_id
        ).scalar()
        
        latest = db.query(PriceData).filter(
            PriceData.asset_id == asset_id
        ).order_by(PriceData.date.desc()).first()
        
        earliest = db.query(PriceData).filter(
            PriceData.asset_id == asset_id
        ).order_by(PriceData.date.asc()).first()
        
        if count > 0:
            print(f"✅ {asset_id}:")
            print(f"   Records: {count}")
            print(f"   Range: {earliest.date} ~ {latest.date}")
            print(f"   Latest price: {latest.close:.2f}")
        else:
            print(f"❌ {asset_id}: No price data")
    
    db.close()
    return True


def test_incremental_update():
    """测试增量更新"""
    print("\n" + "=" * 50)
    print("Test 4: Incremental Update")
    print("=" * 50)
    
    try:
        results = incremental_update(lookback_days=3)
        
        print("✅ Incremental update completed:")
        for r in results:
            status = "✓" if r['status'] == 'success' else "✗"
            print(f"   {status} {r['asset_id']}: {r.get('inserted', 0)} new, {r.get('updated', 0)} updated")
        
        return True
    except Exception as e:
        print(f"❌ Incremental update failed: {e}")
        return False


def test_backfill_history():
    """测试历史数据回填（小范围测试）"""
    print("\n" + "=" * 50)
    print("Test 5: Backfill History (7 days)")
    print("=" * 50)
    
    try:
        start = date.today() - timedelta(days=7)
        results = backfill_all_assets(start=start)
        
        print("✅ Backfill completed:")
        for r in results:
            status = "✓" if r['status'] == 'success' else "✗"
            print(f"   {status} {r['asset_id']}: {r.get('records', 0)} records")
        
        return True
    except Exception as e:
        print(f"❌ Backfill failed: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "🔧" * 25)
    print("Data Terminal - Backfill Tests")
    print("🔧" * 25 + "\n")
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Assets Exist", test_assets_exist),
        ("Price Data", test_price_data),
        ("Incremental Update", test_incremental_update),
        ("Backfill History", test_backfill_history),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
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
