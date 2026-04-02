#!/usr/bin/env python3
"""
价格数据管理 - SQLite 存储和增量更新（长表版本）
"""

import yfinance as yf
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import os
from pathlib import Path


class PriceDataManager:
    """价格数据管理器（长表设计）"""

    # 默认数据库路径
    DEFAULT_DB_PATH = 'data/price_data/prices.db'

    # 支持的交易对配置
    TICKERS = {
        'BTC': 'BTC-USD',
        'GOLD': 'GLD',
        'SPY': 'SPY',
        'HS300': '000300.SS'
    }

    def __init__(self, db_path: str = None, old_db_path: str = None):
        """
        初始化数据管理器

        Args:
            db_path: SQLite 数据库路径（默认为 data/price_data/prices.db）
            old_db_path: 旧数据库路径，用于迁移数据（可选）
        """
        self.db_path = db_path or self.DEFAULT_DB_PATH
        self.old_db_path = old_db_path
        self.ensure_data_dir()
        self.init_database()

        # 如果指定了旧数据库，尝试迁移
        if old_db_path and os.path.exists(old_db_path):
            self.migrate_from_old_db(old_db_path)

    def ensure_data_dir(self):
        """确保 data 目录存在"""
        data_dir = os.path.dirname(self.db_path)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
            print(f"✓ 创建数据目录: {data_dir}")

    def init_database(self):
        """初始化数据库表（长表结构）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 价格数据表（长表设计）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                symbol TEXT NOT NULL,
                close REAL,
                volume REAL,
                UNIQUE(date, symbol)
            )
        ''')

        # 创建索引加速查询
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_date_symbol ON prices(date, symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_symbol ON prices(symbol)')

        # 更新记录表（跟踪数据更新历史）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS update_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                update_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                records_added INTEGER,
                message TEXT
            )
        ''')

        conn.commit()
        conn.close()
        print(f"✓ 数据库初始化完成: {self.db_path}")

    def migrate_from_old_db(self, old_db_path: str):
        """
        从旧数据库迁移数据（宽表 → 长表）

        Args:
            old_db_path: 旧数据库路径
        """
        print(f"\n🔄 从旧数据库迁移数据: {old_db_path}")

        # 检查新数据库是否已有数据
        existing_count = self.get_record_count()
        if existing_count > 0:
            print(f"⚠️  新数据库已有 {existing_count} 条记录，跳过迁移")
            return

        # 从旧数据库读取数据
        old_conn = sqlite3.connect(old_db_path)
        old_data = pd.read_sql_query('SELECT * FROM prices', old_conn)
        old_conn.close()

        if len(old_data) == 0:
            print(f"⚠️  旧数据库为空，跳过迁移")
            return

        # 符号映射（旧表列名 → 新表 symbol）
        symbol_mapping = {
            'btc_close': 'BTC',
            'gold_close': 'GOLD',
            'spy_close': 'SPY',
            'hs300_close': 'HS300'
        }

        # 插入到新数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        migrated_count = 0
        for _, row in old_data.iterrows():
            date_val = row['date']
            for old_col, symbol in symbol_mapping.items():
                price = row.get(old_col)
                if pd.notna(price):
                    try:
                        cursor.execute('''
                            INSERT OR REPLACE INTO prices
                            (date, symbol, close, volume)
                            VALUES (?, ?, ?, ?)
                        ''', (date_val, symbol, float(price), None))
                        migrated_count += 1
                    except Exception as e:
                        print(f"  ⚠️  迁移失败 {date_val} {symbol}: {e}")

        conn.commit()
        conn.close()

        print(f"✓ 迁移完成: {migrated_count} 条记录")

        # 记录迁移日志
        self.log_update(migrated_count, f"从 {old_db_path} 迁移（宽表→长表）")

    def get_record_count(self) -> int:
        """获取数据库记录数量"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM prices')
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def get_latest_date(self) -> str:
        """获取数据库中最新的日期"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT MAX(date) FROM prices')
        result = cursor.fetchone()[0]
        conn.close()
        return result

    def get_earliest_date(self) -> str:
        """获取数据库中最早的日期"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT MIN(date) FROM prices')
        result = cursor.fetchone()[0]
        conn.close()
        return result

    def fetch_prices(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        从 yfinance 获取价格数据（分别下载以避免 MultiIndex 问题）

        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            DataFrame 包含价格数据（长表格式）
        """
        print(f"\n📥 正在获取数据 ({start_date} 至 {end_date})...")

        all_records = []

        for symbol, ticker in self.TICKERS.items():
            print(f"  - 获取 {ticker} ({symbol})...")
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)

            if len(df) == 0:
                print(f"    ⚠️  无数据")
                continue

            # 检查数据结构并提取收盘价
            if isinstance(df.columns, pd.MultiIndex):
                close_col = df[('Close', ticker)]
                volume_col = df.get(('Volume', ticker), pd.Series(index=df.index, dtype=float))
            else:
                close_col = df['Close']
                volume_col = df.get('Volume', pd.Series(index=df.index, dtype=float))

            # 移除时区信息，统一为 UTC
            close_col.index = close_col.index.tz_localize(None)
            volume_col.index = volume_col.index.tz_localize(None)

            # 构建长表格式（只保存非 NaN 的价格数据）
            for idx, (date, close, vol) in enumerate(zip(close_col.index, close_col, volume_col)):
                date_str = date.strftime('%Y-%m-%d %H:%M:%S')
                # 只保存非 NaN 的价格数据
                if pd.notna(close):
                    all_records.append({
                        'date': date_str,
                        'symbol': symbol,
                        'close': float(close),
                        'volume': float(vol) if pd.notna(vol) else None
                    })

        prices_df = pd.DataFrame(all_records)

        if len(prices_df) == 0:
            print(f"⚠️  未获取到任何数据")
            return prices_df

        # 转换日期格式
        prices_df['date'] = pd.to_datetime(prices_df['date']).dt.strftime('%Y-%m-%d %H:%M:%S')

        # 按日期和 symbol 排序
        prices_df = prices_df.sort_values(['date', 'symbol'])

        print(f"✓ 获取到 {len(prices_df)} 条价格记录")
        return prices_df

    def save_prices(self, prices_df: pd.DataFrame):
        """
        保存价格数据到数据库

        Args:
            prices_df: DataFrame 包含价格数据（长表格式）
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        records_added = 0
        records_updated = 0

        for _, row in prices_df.iterrows():
            try:
                date_val = row['date']
                symbol = row['symbol']
                close_val = row['close']
                volume_val = row.get('volume')

                # 检查该日期和 symbol 是否已存在
                cursor.execute(
                    'SELECT 1 FROM prices WHERE date = ? AND symbol = ?',
                    (date_val, symbol)
                )
                exists = cursor.fetchone()

                if not exists:
                    # 新记录，直接插入
                    cursor.execute('''
                        INSERT INTO prices (date, symbol, close, volume)
                        VALUES (?, ?, ?, ?)
                    ''', (date_val, symbol, close_val, volume_val))
                    records_added += 1
                else:
                    # 记录已存在，更新
                    if pd.notna(close_val):
                        cursor.execute('''
                            UPDATE prices
                            SET close = ?, volume = ?
                            WHERE date = ? AND symbol = ?
                        ''', (close_val, volume_val, date_val, symbol))
                        records_updated += 1

            except Exception as e:
                print(f"  ⚠️  保存失败 {row['date']} {row['symbol']}: {e}")

        conn.commit()
        conn.close()

        if records_updated > 0:
            print(f"✓ 新增 {records_added} 条，更新 {records_updated} 条记录到数据库")
        else:
            print(f"✓ 保存 {records_added} 条记录到数据库")

        # 记录更新日志
        self.log_update(records_added + records_updated,
                         f"更新: 新增 {records_added}, 更新 {records_updated}")

    def log_update(self, records_added: int, message: str):
        """记录数据更新日志"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO update_log (records_added, message)
            VALUES (?, ?)
        ''', (records_added, message))
        conn.commit()
        conn.close()

    def load_prices(self, start_date: str = None, end_date: str = None, pivot: bool = True) -> pd.DataFrame:
        """
        从数据库加载价格数据

        Args:
            start_date: 开始日期 (可选）
            end_date: 结束日期 (可选）
            pivot: 是否转换成宽表格式（默认 True，向后兼容）

        Returns:
            DataFrame 包含价格数据
        """
        conn = sqlite3.connect(self.db_path)
        query = 'SELECT * FROM prices'

        if start_date and end_date:
            query += f" WHERE date >= '{start_date}' AND date <= '{end_date}'"
        elif start_date:
            query += f" WHERE date >= '{start_date}'"
        elif end_date:
            query += f" WHERE date <= '{end_date}'"

        query += ' ORDER BY date, symbol'

        df = pd.read_sql_query(query, conn, index_col='id')
        conn.close()

        if len(df) == 0:
            return pd.DataFrame()

        # 转换成宽表格式（向后兼容）
        if pivot:
            df_pivot = df.pivot(index='date', columns='symbol', values='close')

            # 重命名列
            column_mapping = {
                'BTC': 'btc_close',
                'GOLD': 'gold_close',
                'SPY': 'spy_close',
                'HS300': 'hs300_close'
            }
            df_pivot = df_pivot.rename(columns=column_mapping)

            # 确保所有列都存在（按固定顺序）
            for col in ['btc_close', 'gold_close', 'spy_close', 'hs300_close']:
                if col not in df_pivot.columns:
                    df_pivot[col] = None

            df_pivot = df_pivot[['btc_close', 'gold_close', 'spy_close', 'hs300_close']]

            # 转换日期索引
            try:
                df_pivot.index = pd.to_datetime(df_pivot.index, format='%Y-%m-%d %H:%M:%S')
            except ValueError:
                df_pivot.index = pd.to_datetime(df_pivot.index, format='ISO8601')

            return df_pivot
        else:
            # 返回长表格式
            return df

    def load_prices_long(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        从数据库加载价格数据（长表格式）

        Args:
            start_date: 开始日期 (可选）
            end_date: 结束日期 (可选）

        Returns:
            DataFrame 包含价格数据（长表格式）
        """
        return self.load_prices(start_date, end_date, pivot=False)

    def update_prices(self, start_date: str = '2015-01-01', end_date: str = None) -> pd.DataFrame:
        """
        增量更新价格数据

        Args:
            start_date: 基础开始日期（数据库为空时使用）
            end_date: 结束日期（默认为今天）

        Returns:
            DataFrame 包含全部更新后的价格数据（宽表格式）
        """
        # 默认结束日期为今天
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        # 获取数据库最新日期
        latest_date = self.get_latest_date()

        if latest_date:
            # 数据库有数据，增量更新
            print(f"📊 数据库最新日期: {latest_date}")

            # 计算下一个需要下载的日期（最新日期的下一天）
            try:
                latest_dt = datetime.strptime(latest_date, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                latest_dt = datetime.strptime(latest_date, '%Y-%m-%d')

            from_date = (latest_dt + timedelta(days=1)).strftime('%Y-%m-%d')
            today = datetime.now().strftime('%Y-%m-%d')

            if from_date > today:
                print(f"✅ 数据已是最新，无需更新")
                return self.load_prices()

            print(f"🔄 增量更新: {from_date} 至 {end_date}")
            prices_df = self.fetch_prices(from_date, end_date)
        else:
            # 数据库为空，全量下载
            print(f"📊 数据库为空，首次初始化")
            prices_df = self.fetch_prices(start_date, end_date)

        # 保存到数据库
        if len(prices_df) > 0:
            self.save_prices(prices_df)

        # 加载全部数据（宽表格式，向后兼容）
        return self.load_prices()

    def get_update_history(self, limit: int = 10) -> pd.DataFrame:
        """
        获取数据更新历史

        Args:
            limit: 返回的记录数

        Returns:
            DataFrame 包含更新历史
        """
        conn = sqlite3.connect(self.db_path)
        query = f'''
            SELECT * FROM update_log
            ORDER BY update_time DESC
            LIMIT {limit}
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def get_stats(self) -> dict:
        """
        获取数据库统计信息

        Returns:
            统计信息字典
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 记录数
        cursor.execute('SELECT COUNT(*) FROM prices')
        total_records = cursor.fetchone()[0]

        # 日期范围
        cursor.execute('SELECT MIN(date), MAX(date) FROM prices')
        min_date, max_date = cursor.fetchone()

        # 各 symbol 的记录数
        stats = {
            'total_records': total_records,
            'date_range': f"{min_date} 至 {max_date}" if min_date else "无数据",
            'symbol_counts': {}
        }

        for symbol in self.TICKERS.keys():
            cursor.execute(f'SELECT COUNT(*) FROM prices WHERE symbol = ?', (symbol,))
            count = cursor.fetchone()[0]
            stats['symbol_counts'][symbol] = count

        conn.close()
        return stats


# 命令行入口
if __name__ == '__main__':
    import argparse
    import subprocess

    parser = argparse.ArgumentParser(description='价格数据管理工具')
    parser.add_argument('--update', action='store_true', help='更新价格数据')
    parser.add_argument('--migrate', type=str, help='从旧数据库迁移数据')
    parser.add_argument('--stats', action='store_true', help='显示数据库统计信息')
    parser.add_argument('--old-db', type=str, help='旧数据库路径')
    parser.add_argument('--no-plot', action='store_true', help='更新后不生成图表')

    args = parser.parse_args()

    print("=" * 60)
    print("📊 价格数据管理工具")
    print("=" * 60)

    # 初始化数据管理器
    old_db_path = args.old_db if args.old_db else '../portfolio-backtest/data/prices.db'
    manager = PriceDataManager(old_db_path=old_db_path)

    plot_path = None

    # 处理命令
    if args.update:
        print("\n🔄 更新价格数据...")
        prices_df = manager.update_prices()
        print(f"\n✓ 更新完成: {len(prices_df)} 条记录")

        # 自动生成图表（除非 --no-plot）
        if not args.no_plot and len(prices_df) > 0:
            print("\n📊 生成最近一个月的图表...")
            try:
                # 调用 plot_monthly.py
                script_dir = os.path.dirname(os.path.abspath(__file__))
                plot_script = os.path.join(script_dir, 'scripts/plot_monthly.py')
                result = subprocess.run(
                    ['python3', plot_script],
                    capture_output=True,
                    text=True,
                    cwd=script_dir
                )

                if result.returncode == 0:
                    # 从输出中提取文件路径
                    for line in result.stdout.split('\n'):
                        if '✓ 图表已保存:' in line:
                            plot_path = line.split('✓ 图表已保存:')[1].strip()
                            break
                    print(result.stdout)
                else:
                    print(f"⚠️  图表生成失败: {result.stderr}")
            except Exception as e:
                print(f"⚠️  图表生成出错: {e}")

    if args.migrate:
        print(f"\n🔄 从 {args.migrate} 迁移数据...")
        if os.path.exists(args.migrate):
            manager.migrate_from_old_db(args.migrate)
        else:
            print(f"⚠️  文件不存在: {args.migrate}")

    if args.stats:
        print("\n📊 数据库统计信息:")
        stats = manager.get_stats()
        print(f"  总记录数: {stats['total_records']}")
        print(f"  日期范围: {stats['date_range']}")
        print(f"  各资产记录数:")
        for symbol, count in stats['symbol_counts'].items():
            print(f"    {symbol}: {count}")

    # 输出图表路径（供外部脚本使用）
    if plot_path:
        print(f"\n📎 图表文件: {plot_path}")

    # 如果没有指定命令，显示帮助
    if not any([args.update, args.migrate, args.stats]):
        print("\n用法:")
        print("  python3 data_manager.py --update        # 更新价格数据（自动生成图表）")
        print("  python3 data_manager.py --update --no-plot  # 更新但不生成图表")
        print("  python3 data_manager.py --migrate <path>  # 从旧数据库迁移")
        print("  python3 data_manager.py --stats           # 显示统计信息")

    print("\n" + "=" * 60)
