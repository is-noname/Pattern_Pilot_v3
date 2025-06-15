# cache/cache_manager.py - DATETIME CLEANUP VERSION
import os
import sqlite3
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, List
import threading
from utils.logger import logger


class CryptoDataCache:
    """Thread-safe SQLite Cache mit datetime standard"""
    _instance = None  # Singleton-Instanz

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, cache_dir="cache"):
        if self._initialized:
            return
        self._initialized = True
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.db_path = os.path.join(cache_dir, "crypto_cache.db")

        # Thread-lokale Verbindungen statt eine globale
        self._local = threading.local()

        # DB-Schema einmalig initialisieren
        self._init_db_schema()

    def _get_connection(self) -> sqlite3.Connection:
        """Holt oder erstellt Thread-lokale Verbindung"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            # Neue Verbindung für diesen Thread
            self._local.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False  # Erlaubt Thread-Sharing (vorsichtig verwenden)
            )
            print(f"[Cache] Neue DB-Verbindung für Thread {threading.current_thread().ident}")

        return self._local.conn

    def _init_db_schema(self):
        """Einmalige Schema-Initialisierung - DATETIME STANDARD"""
        # Temporäre Verbindung nur für Schema-Setup
        with sqlite3.connect(self.db_path) as conn:
            # Assets-Tabelle
            conn.execute('''
                         CREATE TABLE IF NOT EXISTS assets
                         (
                             asset_id
                             TEXT
                             PRIMARY
                             KEY,
                             symbol
                             TEXT,
                             name
                             TEXT,
                             last_updated
                             TIMESTAMP,
                             data_source
                             TEXT,
                             metadata
                             TEXT
                         )
                         ''')

            # OHLCV-Tabellen für jeden Timeframe - DATETIME COLUMN
            timeframes = ["1h", "1d", "3d", "1w", "1M"]
            for tf in timeframes:
                table_name = f"ohlcv_{tf.replace('M', 'm')}"
                conn.execute(f'''
                CREATE TABLE IF NOT EXISTS {table_name} (
                    asset_id TEXT,
                    datetime TIMESTAMP,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    PRIMARY KEY (asset_id, datetime)
                )
                ''')

                # Index für Datetime-Abfragen
                conn.execute(f'''
                CREATE INDEX IF NOT EXISTS idx_{tf}_datetime ON {table_name} (datetime)
                ''')

            # 🔄 MIGRATION: Rename old 'date' columns to 'datetime' if they exist
            for tf in timeframes:
                table_name = f"ohlcv_{tf.replace('M', 'm')}"
                try:
                    # Check if old 'date' column exists
                    cursor = conn.execute(f"PRAGMA table_info({table_name})")
                    columns = [row[1] for row in cursor.fetchall()]

                    if 'date' in columns and 'datetime' not in columns:
                        print(f"[Cache] Migrating {table_name}: 'date' → 'datetime'")
                        # Rename column
                        conn.execute(f'ALTER TABLE {table_name} RENAME COLUMN date TO datetime')

                        # Drop old index and create new one
                        conn.execute(f'DROP INDEX IF EXISTS idx_{tf}_date')
                        conn.execute(f'''
                        CREATE INDEX IF NOT EXISTS idx_{tf}_datetime ON {table_name} (datetime)
                        ''')
                except Exception as e:
                    print(f"[Cache] Migration warning for {table_name}: {e}")

            conn.commit()
            print("[Cache] DB-Schema mit datetime standard initialisiert")

    def save_asset_data(self, identifier: str, api_result: Dict[str, Any]) -> bool:
        """Speichert Daten (thread-safe) - DATETIME VERSION"""
        if api_result['data'].empty:
            return False

        try:
            conn = self._get_connection()

            # Daten mit datetime standard
            df = api_result['data'].copy()
            metadata = api_result['metadata']
            timeframe = metadata.get('timeframe', '1d')
            tf_key = timeframe.replace('M', 'm')

            # Ensure datetime column exists
            if 'date' in df.columns:
                df = df.rename(columns={'date': 'datetime'})
            if 'datetime' not in df.columns:
                raise ValueError("DataFrame muss 'datetime' column haben")

            # Metadaten speichern
            self._save_asset_metadata(identifier, metadata, conn)

            # OHLCV-Daten speichern
            existing_data = self.get_cached_data(identifier, timeframe)

            if existing_data is not None and not existing_data.empty:
                max_datetime = existing_data['datetime'].max()
                new_data = df[df['datetime'] > max_datetime]
            else:
                new_data = df

            if not new_data.empty:
                new_data = df.copy()  # Explizite Kopie vor Modifikation
                new_data['asset_id'] = identifier
                new_data.to_sql(f"ohlcv_{tf_key}", conn, if_exists='append', index=False)
                conn.commit()
                logger.cache_info(f"{len(new_data)} Datenpunkte gespeichert")
                print(f"[Cache] {len(new_data)} Datenpunkte gespeichert")

            return True

        except Exception as e:
            print(f"[Cache] Speicher-Fehler: {e}")
            return False

    def _save_asset_metadata(self, identifier: str, metadata: Dict[str, Any], conn: sqlite3.Connection):
        """Metadaten speichern (mit übergebener Verbindung)"""
        import json

        meta_json = json.dumps({k: v for k, v in metadata.items()
                                if k not in ['identifier', 'symbol', 'name']})

        conn.execute('''
                     INSERT INTO assets (asset_id, symbol, name, last_updated, data_source, metadata)
                     VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(asset_id) DO
                     UPDATE SET
                         symbol = excluded.symbol,
                         name = excluded.name,
                         last_updated = excluded.last_updated,
                         data_source = excluded.data_source,
                         metadata = excluded.metadata
                     ''', (
                         identifier,
                         metadata.get('symbol', ''),
                         metadata.get('name', ''),
                         datetime.now().isoformat(),
                         metadata.get('source_api', 'unknown'),
                         meta_json
                     ))

    def get_cached_data(self, identifier: str, timeframe: str = "1d") -> Optional[pd.DataFrame]:
        """Lädt gecachte Daten (thread-safe) - DATETIME VERSION"""
        tf_key = timeframe.replace('M', 'm')

        try:
            conn = self._get_connection()

            query = f'''
                    SELECT datetime, open, high, low, close, volume 
                    FROM ohlcv_{tf_key}
                    WHERE asset_id = ?
                    AND datetime IS NOT NULL AND datetime != ''
                    ORDER BY datetime
            '''

            df = pd.read_sql_query(query, conn, params=(identifier,))

            if not df.empty:
                # 🛡️ ROBUSTE DATETIME-KONVERTIERUNG
                try:
                    # Vor Konvertierung bereinigen
                    df['datetime'] = df['datetime'].replace('', pd.NaT)
                    df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce', utc=False)

                    # NaT-Zeilen entfernen
                    initial_len = len(df)
                    df = df.dropna(subset=['datetime']).reset_index(drop=True)

                    if len(df) < initial_len:
                        logger.cache_info(f"Cache: {initial_len - len(df)} invalid dates removed")

                    return df if not df.empty else None

                except Exception as e:
                    print(f"❌ [Cache] Datetime conversion failed: {e}")
                    return None

            return None

        except Exception as e:
            print(f"❌ [Cache] Load error: {e}")
            return None

    def get_available_assets(self) -> List[Dict[str, Any]]:
        """Gibt alle verfügbaren Assets zurück (thread-safe)"""
        try:
            conn = self._get_connection()
            query = '''
            SELECT asset_id, symbol, name, last_updated, data_source
            FROM assets
            ORDER BY symbol \
            '''

            df = pd.read_sql_query(query, conn)
            return df.to_dict('records')

        except Exception as e:
            print(f"[Cache] Asset-Liste Fehler: {e}")
            return []

    def get_available_timeframes(self, identifier: str) -> List[str]:
        """Gibt verfügbare Timeframes für ein Asset zurück (thread-safe)"""
        try:
            conn = self._get_connection()
            available = []
            timeframes = ["1h", "1d", "3d", "1w", "1M"]

            for tf in timeframes:
                tf_key = tf.replace('M', 'm')
                query = f'''
                SELECT COUNT(*) as count
                FROM ohlcv_{tf_key}
                WHERE asset_id = ?
                '''

                cursor = conn.execute(query, (identifier,))
                result = cursor.fetchone()

                if result and result[0] > 0:
                    available.append(tf)

            return available

        except Exception as e:
            print(f"[Cache] Timeframes-Fehler: {e}")
            return []

    def clear_asset_data(self, identifier: str, timeframe: Optional[str] = None):
        """Löscht Daten für ein Asset (thread-safe)"""
        try:
            conn = self._get_connection()

            if timeframe:
                # Nur bestimmten Timeframe löschen
                tf_key = timeframe.replace('M', 'm')
                conn.execute(f'''
                DELETE FROM ohlcv_{tf_key} WHERE asset_id = ?
                ''', (identifier,))
                print(f"[Cache] {identifier} ({timeframe}) gelöscht")
            else:
                # Alle Timeframes löschen
                for tf in ["1h", "1d", "3d", "1w", "1M"]:
                    tf_key = tf.replace('M', 'm')
                    conn.execute(f'''
                    DELETE FROM ohlcv_{tf_key} WHERE asset_id = ?
                    ''', (identifier,))

                # Asset-Metadaten löschen
                conn.execute('''
                DELETE FROM assets WHERE asset_id = ?
                ''', (identifier,))
                print(f"[Cache] {identifier} komplett gelöscht")

            conn.commit()

        except Exception as e:
            print(f"[Cache] Löschfehler: {e}")
            if hasattr(self._local, 'conn') and self._local.conn:
                self._local.conn.rollback()

    def close(self):
        """Schließt Thread-lokale Verbindungen"""
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None
            print("[Cache] Verbindung geschlossen")


cache_instance = CryptoDataCache()