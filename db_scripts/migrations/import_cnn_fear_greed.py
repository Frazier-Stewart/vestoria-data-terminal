"""Import CNN Fear & Greed historical data into database."""
import asyncio
import sys
sys.path.insert(0, '.')

from datetime import date
from app.core.database import SessionLocal
from app.indicators.cnn_fear_greed import CNNFearGreedIndicator
from app.models.indicator import Indicator, IndicatorValue


def import_cnn_fear_greed():
    """Import all historical CNN Fear & Greed data."""
    db = SessionLocal()
    try:
        # Find the CNN_FEAR_GREED indicator instance
        indicator = db.query(Indicator).filter(
            Indicator.template_id == "CNN_FEAR_GREED"
        ).first()

        if not indicator:
            print("CNN_FEAR_GREED indicator not found. Please restart the backend first to initialize.")
            return

        indicator_id = indicator.id
        print(f"Importing CNN Fear & Greed data for indicator_id={indicator_id}")

        # Clear existing values
        deleted = db.query(IndicatorValue).filter(
            IndicatorValue.indicator_id == indicator_id
        ).delete()
        db.commit()
        print(f"Cleared {deleted} old values")

        # Calculate all historical data (2011 to today)
        processor = CNNFearGreedIndicator()
        results = asyncio.run(processor.calculate(
            asset_id="^GSPC",
            start=date(2011, 1, 1),
            end=date.today()
        ))

        if not results:
            print("No data returned from processor")
            return

        print(f"Calculated {len(results)} values")

        # Bulk insert
        from sqlalchemy.dialects.sqlite import insert

        for result in results:
            db_value = IndicatorValue(
                indicator_id=indicator_id,
                date=result.date,
                timestamp=result.timestamp,
                value=result.value,
                value_text=result.value_text,
                grade=result.grade,
                grade_label=result.grade_label,
                extra_data=result.extra_data or {},
                source="cnn_fear_greed_csv",
            )
            db.add(db_value)

        db.commit()
        print(f"Successfully imported {len(results)} CNN Fear & Greed values")
        print(f"Date range: {results[0].date} to {results[-1].date}")

    except Exception as e:
        db.rollback()
        print(f"Error importing CNN Fear & Greed data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import_cnn_fear_greed()
