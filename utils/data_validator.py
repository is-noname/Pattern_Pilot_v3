# utils/data_validator.py
import pandas as pd
from typing import Dict, Any, List, Tuple


class DataValidator:
    """
    Validiert und bewertet OHLCV-Datenqualität
    """
    
    @staticmethod
    def validate_ohlcv(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Comprehensive OHLCV-Datenvalidierung
        
        Returns:
            {
                'is_valid': bool,
                'quality_score': int (0-100),
                'issues': List[str],
                'warnings': List[str],
                'stats': Dict[str, Any]
            }
        """
        if df.empty:
            return {
                'is_valid': False,
                'quality_score': 0,
                'issues': ['DataFrame ist leer'],
                'warnings': [],
                'stats': {}
            }
        
        issues = []
        warnings = []
        score = 100
        
        # 1. Strukturvalidierung
        required_cols = ['open', 'high', 'low', 'close']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            issues.append(f"Fehlende Spalten: {missing_cols}")
            score -= 30
        
        # 2. Index-Validierung
        if not isinstance(df.index, pd.DatetimeIndex):
            issues.append("Index ist kein DatetimeIndex")
            score -= 20
        
        # 3. Datentyp-Validierung
        numeric_cols = [col for col in ['open', 'high', 'low', 'close', 'volume'] if col in df.columns]
        for col in numeric_cols:
            if not pd.api.types.is_numeric_dtype(df[col]):
                issues.append(f"Spalte {col} ist nicht numerisch")
                score -= 10
        
        # 4. Fehlende Werte
        null_counts = df.isnull().sum()
        total_nulls = null_counts.sum()
        if total_nulls > 0:
            null_pct = (total_nulls / (len(df) * len(df.columns))) * 100
            if null_pct > 50:
                issues.append(f"Zu viele fehlende Werte: {null_pct:.1f}%")
                score -= 30
            elif null_pct > 10:
                warnings.append(f"Viele fehlende Werte: {null_pct:.1f}%")
                score -= 10
        
        # 5. OHLC-Logik prüfen
        if all(col in df.columns for col in required_cols):
            ohlc_issues = DataValidator._validate_ohlc_logic(df)
            if ohlc_issues:
                warnings.extend(ohlc_issues)
                score -= min(len(ohlc_issues) * 5, 20)
        
        # 6. Preisvariation prüfen
        if 'close' in df.columns:
            price_variation = DataValidator._check_price_variation(df['close'])
            if not price_variation['has_variation']:
                issues.append("Keine Preisvariation - konstante Werte")
                score -= 40
            elif price_variation['low_variation']:
                warnings.append("Geringe Preisvariation")
                score -= 15
        
        # 7. Volume-Validierung
        if 'volume' in df.columns:
            volume_issues = DataValidator._validate_volume(df['volume'])
            warnings.extend(volume_issues)
            score -= min(len(volume_issues) * 3, 15)
        
        # 8. Datenlücken prüfen
        gaps = DataValidator._detect_time_gaps(df)
        if gaps['large_gaps'] > 0:
            warnings.append(f"{gaps['large_gaps']} große Zeitlücken erkannt")
            score -= min(gaps['large_gaps'] * 2, 10)
        
        # Statistiken erstellen
        stats = DataValidator._calculate_stats(df)
        
        # Final Score begrenzen
        score = max(0, min(100, score))
        
        return {
            'is_valid': len(issues) == 0,
            'quality_score': score,
            'issues': issues,
            'warnings': warnings,
            'stats': stats
        }
    
    @staticmethod
    def _validate_ohlc_logic(df: pd.DataFrame) -> List[str]:
        """
        Prüft OHLC-Logik (High >= Open,Close,Low etc.)
        """
        issues = []
        
        # High sollte höchster Wert sein
        high_violations = (
            (df['high'] < df['open']) | 
            (df['high'] < df['close']) | 
            (df['high'] < df['low'])
        ).sum()
        
        if high_violations > 0:
            issues.append(f"{high_violations} High-Wert Verletzungen")
        
        # Low sollte niedrigster Wert sein
        low_violations = (
            (df['low'] > df['open']) | 
            (df['low'] > df['close']) | 
            (df['low'] > df['high'])
        ).sum()
        
        if low_violations > 0:
            issues.append(f"{low_violations} Low-Wert Verletzungen")
        
        return issues
    
    @staticmethod
    def _check_price_variation(prices: pd.Series) -> Dict[str, Any]:
        """
        Prüft Preisvariation
        """
        unique_values = prices.nunique()
        total_values = len(prices)
        
        if unique_values == 1:
            return {'has_variation': False, 'low_variation': False}
        
        # Coefficient of Variation
        cv = prices.std() / prices.mean() if prices.mean() != 0 else 0
        
        return {
            'has_variation': True,
            'low_variation': cv < 0.01,  # Weniger als 1% Variation
            'coefficient_of_variation': cv,
            'unique_ratio': unique_values / total_values
        }
    
    @staticmethod
    def _validate_volume(volume: pd.Series) -> List[str]:
        """
        Validiert Volume-Daten
        """
        issues = []
        
        # Negative Volume prüfen
        negative_count = (volume < 0).sum()
        if negative_count > 0:
            issues.append(f"{negative_count} negative Volume-Werte")
        
        # Null-Volume prüfen
        zero_count = (volume == 0).sum()
        zero_pct = (zero_count / len(volume)) * 100
        if zero_pct > 50:
            issues.append(f"{zero_pct:.1f}% Null-Volume")
        elif zero_pct > 20:
            issues.append(f"{zero_pct:.1f}% Null-Volume (moderat)")
        
        return issues
    
    @staticmethod
    def _detect_time_gaps(df: pd.DataFrame) -> Dict[str, int]:
        """
        Erkennt Zeitlücken in den Daten
        """
        if len(df) < 2:
            return {'large_gaps': 0, 'small_gaps': 0}
        
        # Zeitdifferenzen berechnen
        time_diffs = df.index.to_series().diff().dropna()
        
        # "Normale" Intervall-Größe schätzen (Median)
        normal_interval = time_diffs.median()
        
        # Große Lücken = mehr als 3x normales Intervall
        large_gaps = (time_diffs > normal_interval * 3).sum()
        
        # Kleine Lücken = 1.5-3x normales Intervall  
        small_gaps = ((time_diffs > normal_interval * 1.5) & (time_diffs <= normal_interval * 3)).sum()
        
        return {
            'large_gaps': large_gaps,
            'small_gaps': small_gaps
        }
    
    @staticmethod
    def _calculate_stats(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Berechnet Datenstatistiken
        """
        stats = {
            'total_records': len(df),
            'date_range': {
                'start': df.index.min().isoformat() if not df.empty else None,
                'end': df.index.max().isoformat() if not df.empty else None,
                'days': (df.index.max() - df.index.min()).days if not df.empty else 0
            },
            'available_columns': list(df.columns)
        }
        
        # Preis-Statistiken
        if 'close' in df.columns:
            stats['price_stats'] = {
                'min': float(df['close'].min()),
                'max': float(df['close'].max()),
                'mean': float(df['close'].mean()),
                'std': float(df['close'].std())
            }
        
        # Volume-Statistiken
        if 'volume' in df.columns:
            stats['volume_stats'] = {
                'total': float(df['volume'].sum()),
                'mean_daily': float(df['volume'].mean()),
                'max_daily': float(df['volume'].max())
            }
        
        return stats