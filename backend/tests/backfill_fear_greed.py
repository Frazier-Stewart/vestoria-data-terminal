#!/usr/bin/env python3
"""
补充 BTC 恐慌贪婪指数历史数据

Usage:
    python tests/backfill_fear_greed.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
import requests
from datetime import date, datetime, timedelta
from app.core.database import SessionLocal
from app.models.indicator import Indicator, IndicatorValue


def fetch_fear_greed_history(limit=1000):
    """从 API 获取历史数据"""
    url = "https://api.alternative.me/fng/"
    
    try:
        response = requests.get(
            url,
            params={"limit": limit, "format": "json"},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ API request failed: {e}")
        return None


def save_to_database(indicator_id, data):
    """保存数据到数据库"""
    db = SessionLocal()
    
    inserted = 0
    updated = 0
    skipped = 0
    
    # Grading mapping
    def get_grade(value):
        if value < 25:
            return 1, "极度恐惧"
        elif value < 50:
            return 2, "恐惧"
        elif value < 55:
            return 3, "中性"
        elif value < 75:
            return 4, "贪婪"
        else:
            return 5, "极度贪婪"
    
    def get_chinese_label(classification):
        mapping = {
            "Extreme Fear": "极度恐惧",
            "Fear": "恐惧",
            "Neutral": "中性",
            "Greed": "贪婪",
            "Extreme Greed": "极度贪婪",
        }
        return mapping.get(classification, classification)
    
    for item in data:
        try:
            # Parse timestamp
            timestamp = datetime.fromtimestamp(int(item["timestamp"]))
            value = float(item["value"])
            classification = item.get("value_classification", "")
            
            grade, grade_label = get_grade(value)
            value_text = get_chinese_label(classification)
            
            # Check if record exists
            existing = db.query(IndicatorValue).filter(
                IndicatorValue.indicator_id == indicator_id,
                IndicatorValue.date == timestamp.date()
            ).first()
            
            if existing:
                # Update
                existing.value = value
                existing.value_text = value_text
                existing.grade = grade
                existing.grade_label = grade_label
                existing.timestamp = timestamp
                existing.source = "alternative.me"
                updated += 1
            else:
                # Create new
                db_value = IndicatorValue(
                    indicator_id=indicator_id,
                    date=timestamp.date(),
                    timestamp=timestamp,
                    value=value,
                    value_text=value_text,
                    grade=grade,
                    grade_label=grade_label,
                    source="alternative.me"
                )
                db.add(db_value)
                inserted += 1
                
        except Exception as e:
            print(f"⚠️  Error processing item: {e}")
            skipped += 1
            continue
    
    db.commit()
    db.close()
    
    return inserted, updated, skipped


def main():
    print("=" * 60)
    print("BTC Fear & Greed Index - Historical Data Backfill")
    print("=" * 60)
    
    # Get indicator
    db = SessionLocal()
    indicator = db.query(Indicator).filter(
        Indicator.template_id == "BTC_FEAR_GREED"
    ).first()
    
    if not indicator:
        print("❌ BTC Fear & Greed indicator not found in database")
        db.close()
        return
    
    print(f"✅ Found indicator: {indicator.name} (ID: {indicator.id})")
    
    # Check current data
    current_count = db.query(IndicatorValue).filter(
        IndicatorValue.indicator_id == indicator.id
    ).count()
    
    if current_count > 0:
        latest = db.query(IndicatorValue).filter(
            IndicatorValue.indicator_id == indicator.id
        ).order_by(IndicatorValue.date.desc()).first()
        earliest = db.query(IndicatorValue).filter(
            IndicatorValue.indicator_id == indicator.id
        ).order_by(IndicatorValue.date.asc()).first()
        
        print(f"📊 Current data: {current_count} records")
        print(f"   Range: {earliest.date} to {latest.date}")
    
    db.close()
    
    # Fetch from API
    print("\n🌐 Fetching data from alternative.me API...")
    data = fetch_fear_greed_history(limit=1000)
    
    if not data or "data" not in data:
        print("❌ Failed to fetch data from API")
        return
    
    api_records = data["data"]
    print(f"✅ Received {len(api_records)} records from API")
    
    # Show date range from API
    first_ts = datetime.fromtimestamp(int(api_records[-1]["timestamp"]))
    last_ts = datetime.fromtimestamp(int(api_records[0]["timestamp"]))
    print(f"   API range: {first_ts.date()} to {last_ts.date()}")
    
    # Save to database
    print("\n💾 Saving to database...")
    inserted, updated, skipped = save_to_database(indicator.id, api_records)
    
    print(f"\n✅ Done!")
    print(f"   Inserted: {inserted}")
    print(f"   Updated: {updated}")
    print(f"   Skipped: {skipped}")
    
    # Verify final state
    db = SessionLocal()
    final_count = db.query(IndicatorValue).filter(
        IndicatorValue.indicator_id == indicator.id
    ).count()
    final_earliest = db.query(IndicatorValue).filter(
        IndicatorValue.indicator_id == indicator.id
    ).order_by(IndicatorValue.date.asc()).first()
    final_latest = db.query(IndicatorValue).filter(
        IndicatorValue.indicator_id == indicator.id
    ).order_by(IndicatorValue.date.desc()).first()
    db.close()
    
    print(f"\n📊 Final state:")
    print(f"   Total records: {final_count}")
    print(f"   Range: {final_earliest.date} to {final_latest.date}")


if __name__ == "__main__":
    main()
