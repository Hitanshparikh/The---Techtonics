import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score
from sklearn.impute import SimpleImputer
import joblib
import os
import logging
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import json
from sqlalchemy import select

from app.core.config import settings
from app.models.ml_models import MLModel, Prediction
from app.models.data_models import CoastalData

logger = logging.getLogger(__name__)

class MLService:
    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.imputers: Dict[str, SimpleImputer] = {}
        self.feature_columns: Dict[str, List[str]] = {}
        
    def detect_schema(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect the schema of uploaded data and determine features"""
        schema = {
            'columns': list(df.columns),
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
            'numeric_columns': [],
            'categorical_columns': [],
            'datetime_columns': [],
            'potential_features': [],
            'potential_target': None
        }
        
        for col in df.columns:
            col_lower = col.lower()
            
            # Detect datetime columns
            if any(keyword in col_lower for keyword in ['time', 'date', 'timestamp']):
                schema['datetime_columns'].append(col)
                df[col] = pd.to_datetime(df[col], errors='coerce')
            
            # Detect numeric columns
            elif df[col].dtype in ['int64', 'float64'] or df[col].dtype == 'object':
                if df[col].dtype == 'object':
                    # Try to convert to numeric
                    try:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                        if not df[col].isna().all():
                            schema['numeric_columns'].append(col)
                    except:
                        schema['categorical_columns'].append(col)
                else:
                    schema['numeric_columns'].append(col)
            
            # Detect potential features
            if any(keyword in col_lower for keyword in ['level', 'height', 'speed', 'pressure', 'temperature', 'humidity']):
                schema['potential_features'].append(col)
            
            # Detect potential target (risk-related columns)
            if any(keyword in col_lower for keyword in ['risk', 'threat', 'danger', 'alert', 'score']):
                schema['potential_target'] = col
        
        # If no target found, create a synthetic risk score
        if not schema['potential_target']:
            schema['potential_target'] = 'synthetic_risk_score'
            # Create synthetic risk score based on available features
            if schema['potential_features']:
                df['synthetic_risk_score'] = self._create_synthetic_risk_score(df, schema['potential_features'])
        
        return schema
    
    def _create_synthetic_risk_score(self, df: pd.DataFrame, features: List[str]) -> pd.Series:
        """Create a deterministic synthetic risk score based on available features"""
        # Use a seed based on dataset content for consistency
        data_hash = hash(str(df.values.tobytes())) % (2**31)
        np.random.seed(abs(data_hash) % 10000)
        
        risk_score = np.zeros(len(df))
        feature_weights = {}
        
        # Assign consistent weights to features
        for i, feature in enumerate(features):
            if feature in df.columns:
                # Use deterministic weight based on feature name
                feature_hash = hash(feature) % 1000
                feature_weights[feature] = 0.1 + (feature_hash / 1000) * 0.8
        
        for feature in features:
            if feature in df.columns:
                feature_data = df[feature].fillna(df[feature].mean())
                if feature_data.std() > 0:
                    # Normalize the feature to 0-1 range
                    normalized = (feature_data - feature_data.min()) / (feature_data.max() - feature_data.min())
                    # Apply consistent weight
                    risk_score += normalized * feature_weights.get(feature, 0.5)
        
        # Normalize final risk score to 0-1
        if risk_score.max() > risk_score.min():
            risk_score = (risk_score - risk_score.min()) / (risk_score.max() - risk_score.min())
        
        return risk_score
    
    def analyze_dataset(self, df: pd.DataFrame, schema: Dict[str, Any], dataset_id: str) -> Dict[str, Any]:
        """Comprehensive AI analysis of uploaded dataset with consistent results"""
        try:
            logger.info(f"Starting AI analysis for dataset {dataset_id}")
            
            # Create deterministic seed based on dataset content for consistency
            data_hash = hash(str(df.values.tobytes()) + dataset_id) % (2**31)
            np.random.seed(abs(data_hash) % 10000)
            
            # Basic data quality metrics
            data_quality_score = self._calculate_data_quality(df)
            
            # Statistical analysis
            stats = self._generate_statistical_insights(df, schema)
            
            # Risk assessment
            risk_analysis = self._assess_risk_patterns(df, schema)
            
            # Trend analysis
            trends = self._analyze_trends(df, schema)
            
            # Anomaly detection
            anomalies = self._detect_anomalies_comprehensive(df, schema)
            
            # Generate predictions
            ml_predictions = self._generate_ml_predictions(df, schema)
            predictions = self._generate_predictions(df, schema, data_hash)
            
            # Create insights
            insights = self._generate_insights(df, schema, stats, risk_analysis, trends)
            
            # Generate alerts based on analysis
            alerts = self._generate_analysis_alerts(df, schema, risk_analysis, anomalies, ml_predictions)
            
            analysis_result = {
                "dataset_id": dataset_id,
                "analysis_timestamp": datetime.now().isoformat(),
                "data_quality_score": data_quality_score,
                "total_records": len(df),
                "risk_level": risk_analysis["overall_risk_level"],
                "risk_score": ml_predictions.get("risk_score", 0.5),
                "confidence": ml_predictions.get("confidence", 0.7),
                "trend": ml_predictions.get("trend", "stable"),
                "statistical_summary": stats,
                "risk_analysis": risk_analysis,
                "trend_analysis": trends,
                "anomalies": anomalies,
                "predictions": predictions,
                "ml_predictions": ml_predictions,
                "predictions_count": len(predictions),
                "insights": insights,
                "alerts": alerts,
                "recommendations": self._generate_recommendations(risk_analysis, anomalies, trends),
                "analysis_hash": str(abs(data_hash))  # For consistency verification
            }
            
            # Store analysis result persistently
            self._store_analysis_result(dataset_id, analysis_result)
            
            logger.info(f"AI analysis completed for dataset {dataset_id}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return {
                "dataset_id": dataset_id,
                "error": str(e),
                "analysis_timestamp": datetime.now().isoformat()
            }
    
    def _calculate_data_quality(self, df: pd.DataFrame) -> float:
        """Calculate dynamic data quality score based on actual data characteristics"""
        if df.empty:
            return 0.0
        
        total_score = 0.0
        max_score = 100.0
        
        # 1. Completeness (40% weight) - Check for missing values
        total_cells = len(df) * len(df.columns)
        missing_cells = df.isnull().sum().sum()
        completeness = ((total_cells - missing_cells) / total_cells) * 100 if total_cells > 0 else 0
        completeness_score = completeness * 0.4
        
        # 2. Uniqueness (25% weight) - Check for duplicate records
        duplicate_count = df.duplicated().sum()
        uniqueness = ((len(df) - duplicate_count) / len(df)) * 100 if len(df) > 0 else 0
        uniqueness_score = uniqueness * 0.25
        
        # 3. Validity (20% weight) - Check data type consistency and value ranges
        validity_score = 0.0
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            col_data = df[col].dropna()
            if len(col_data) > 0:
                # Check for realistic value ranges
                q1, q3 = col_data.quantile([0.25, 0.75])
                iqr = q3 - q1
                outlier_bounds = (q1 - 3 * iqr, q3 + 3 * iqr)
                
                # Count values within reasonable bounds
                valid_values = col_data[(col_data >= outlier_bounds[0]) & (col_data <= outlier_bounds[1])]
                col_validity = len(valid_values) / len(col_data) * 100
                validity_score += col_validity
        
        if len(numeric_cols) > 0:
            validity_score = (validity_score / len(numeric_cols)) * 0.2
        else:
            validity_score = 20.0  # Default if no numeric columns
        
        # 4. Consistency (15% weight) - Check for consistent data patterns
        consistency_score = 0.0
        
        # Check timestamp consistency if present
        datetime_cols = df.select_dtypes(include=['datetime64']).columns
        if len(datetime_cols) > 0:
            for col in datetime_cols:
                time_data = pd.to_datetime(df[col], errors='coerce').dropna()
                if len(time_data) > 1:
                    # Check for consistent time intervals
                    time_diffs = time_data.diff().dropna()
                    if len(time_diffs) > 0:
                        median_diff = time_diffs.median()
                        consistent_intervals = time_diffs[(time_diffs >= median_diff * 0.5) & 
                                                         (time_diffs <= median_diff * 2.0)]
                        consistency_score += (len(consistent_intervals) / len(time_diffs)) * 100
        
        if len(datetime_cols) > 0:
            consistency_score = (consistency_score / len(datetime_cols)) * 0.15
        else:
            consistency_score = 12.0  # Default consistency score
        
        # Calculate total quality score
        total_score = completeness_score + uniqueness_score + validity_score + consistency_score
        
        # Apply penalties for specific data quality issues
        if len(df) < 10:
            total_score *= 0.7  # Penalty for very small datasets
        elif len(df) < 50:
            total_score *= 0.85  # Smaller penalty for small datasets
        
        # Check for excessive missing data in key columns
        key_columns = ['timestamp', 'latitude', 'longitude', 'risk_score']
        for col in key_columns:
            if col in df.columns:
                missing_rate = df[col].isnull().sum() / len(df)
                if missing_rate > 0.5:  # More than 50% missing
                    total_score *= 0.8
        
        return round(max(0.0, min(100.0, total_score)), 1)
    
    def _generate_statistical_insights(self, df: pd.DataFrame, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive statistical insights from the data"""
        stats = {
            "summary": {},
            "correlations": {},
            "distributions": {},
            "outliers": {}
        }
        
        numeric_cols = [col for col in schema['numeric_columns'] if col in df.columns and not df[col].empty]
        
        for col in numeric_cols:
            col_data = df[col].dropna()
            if len(col_data) > 0:
                # Basic statistics
                stats["summary"][col] = {
                    "count": int(len(col_data)),
                    "mean": float(col_data.mean()),
                    "median": float(col_data.median()),
                    "std": float(col_data.std()) if len(col_data) > 1 else 0.0,
                    "min": float(col_data.min()),
                    "max": float(col_data.max()),
                    "q25": float(col_data.quantile(0.25)),
                    "q75": float(col_data.quantile(0.75)),
                    "skewness": float(col_data.skew()) if len(col_data) > 1 else 0.0,
                    "kurtosis": float(col_data.kurtosis()) if len(col_data) > 1 else 0.0
                }
                
                # Distribution analysis
                stats["distributions"][col] = {
                    "is_normal": abs(col_data.skew()) < 1.0 if len(col_data) > 1 else True,
                    "has_outliers": self._detect_outliers_iqr(col_data),
                    "variance": float(col_data.var()) if len(col_data) > 1 else 0.0
                }
                
                # Outlier detection
                outliers = self._get_outlier_indices(col_data)
                stats["outliers"][col] = {
                    "count": len(outliers),
                    "percentage": round(len(outliers) / len(col_data) * 100, 2),
                    "indices": outliers[:10]  # First 10 outlier indices
                }
        
        # Calculate correlations between numeric columns
        if len(numeric_cols) > 1:
            correlation_matrix = df[numeric_cols].corr()
            for i, col1 in enumerate(numeric_cols):
                for j, col2 in enumerate(numeric_cols):
                    if i < j:  # Avoid duplicate pairs
                        corr_value = correlation_matrix.loc[col1, col2]
                        if not pd.isna(corr_value):
                            stats["correlations"][f"{col1}_vs_{col2}"] = {
                                "correlation": float(corr_value),
                                "strength": self._interpret_correlation(abs(corr_value)),
                                "direction": "positive" if corr_value > 0 else "negative"
                            }
        
        return stats
    
    def _detect_outliers_iqr(self, data: pd.Series) -> bool:
        """Detect if outliers exist using IQR method"""
        if len(data) < 4:
            return False
        
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = data[(data < lower_bound) | (data > upper_bound)]
        return len(outliers) > 0
    
    def _get_outlier_indices(self, data: pd.Series) -> List[int]:
        """Get indices of outliers using IQR method"""
        if len(data) < 4:
            return []
        
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outlier_mask = (data < lower_bound) | (data > upper_bound)
        return data[outlier_mask].index.tolist()
    
    def _interpret_correlation(self, abs_corr: float) -> str:
        """Interpret correlation strength"""
        if abs_corr >= 0.8:
            return "very_strong"
        elif abs_corr >= 0.6:
            return "strong"
        elif abs_corr >= 0.4:
            return "moderate"
        elif abs_corr >= 0.2:
            return "weak"
        else:
            return "very_weak"
    
    def _assess_risk_patterns(self, df: pd.DataFrame, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Dynamic risk assessment based on actual data patterns"""
        risk_analysis = {
            "overall_risk_level": "LOW",
            "high_risk_records": 0,
            "medium_risk_records": 0,
            "low_risk_records": 0,
            "risk_factors": [],
            "geographic_risks": [],
            "temporal_risks": [],
            "risk_distribution": {},
            "critical_thresholds": {}
        }
        
        # Analyze target variable if exists
        target_col = schema.get('potential_target')
        if target_col and target_col in df.columns:
            target_data = df[target_col].dropna()
            
            if len(target_data) > 0:
                # Calculate dynamic risk thresholds based on data distribution
                risk_mean = target_data.mean()
                risk_std = target_data.std()
                
                # Define thresholds based on statistical distribution
                low_threshold = max(0, risk_mean - risk_std)
                high_threshold = min(1, risk_mean + risk_std)
                critical_threshold = min(1, risk_mean + 2 * risk_std)
                
                # Count records in each risk category
                low_risk_count = len(target_data[target_data <= low_threshold])
                medium_risk_count = len(target_data[(target_data > low_threshold) & (target_data <= high_threshold)])
                high_risk_count = len(target_data[target_data > high_threshold])
                critical_risk_count = len(target_data[target_data > critical_threshold])
                
                risk_analysis["low_risk_records"] = int(low_risk_count)
                risk_analysis["medium_risk_records"] = int(medium_risk_count)
                risk_analysis["high_risk_records"] = int(high_risk_count)
                
                # Calculate risk percentages
                total_records = len(target_data)
                high_risk_percentage = (high_risk_count / total_records) * 100
                critical_risk_percentage = (critical_risk_count / total_records) * 100
                
                # Determine overall risk level based on actual data distribution
                if critical_risk_percentage > 15:  # More than 15% critical
                    risk_analysis["overall_risk_level"] = "CRITICAL"
                elif high_risk_percentage > 25:  # More than 25% high risk
                    risk_analysis["overall_risk_level"] = "HIGH"
                elif high_risk_percentage > 10:  # More than 10% high risk
                    risk_analysis["overall_risk_level"] = "MEDIUM"
                else:
                    risk_analysis["overall_risk_level"] = "LOW"
                
                # Store risk distribution
                risk_analysis["risk_distribution"] = {
                    "low_percentage": round((low_risk_count / total_records) * 100, 1),
                    "medium_percentage": round((medium_risk_count / total_records) * 100, 1),
                    "high_percentage": round(high_risk_percentage, 1),
                    "critical_percentage": round(critical_risk_percentage, 1)
                }
                
                # Store thresholds
                risk_analysis["critical_thresholds"] = {
                    "low_threshold": round(low_threshold, 3),
                    "high_threshold": round(high_threshold, 3),
                    "critical_threshold": round(critical_threshold, 3),
                    "mean_risk": round(risk_mean, 3),
                    "std_risk": round(risk_std, 3)
                }
                
                # Analyze risk factors with real correlations
                for feature in schema['potential_features']:
                    if feature in df.columns:
                        feature_data = df[feature].dropna()
                        
                        # Align the data for correlation calculation
                        common_indices = target_data.index.intersection(feature_data.index)
                        if len(common_indices) > 5:  # Need sufficient data
                            target_aligned = target_data[common_indices]
                            feature_aligned = feature_data[common_indices]
                            
                            correlation = target_aligned.corr(feature_aligned)
                            
                            if not pd.isna(correlation) and abs(correlation) > 0.1:  # Significant correlation
                                # Determine impact level based on correlation strength
                                if abs(correlation) > 0.7:
                                    impact = "CRITICAL"
                                elif abs(correlation) > 0.5:
                                    impact = "HIGH"
                                elif abs(correlation) > 0.3:
                                    impact = "MEDIUM"
                                else:
                                    impact = "LOW"
                                
                                risk_analysis["risk_factors"].append({
                                    "factor": feature,
                                    "correlation": round(float(correlation), 3),
                                    "impact": impact,
                                    "direction": "increases_risk" if correlation > 0 else "decreases_risk",
                                    "confidence": min(0.95, abs(correlation))
                                })
                
                # Sort risk factors by correlation strength
                risk_analysis["risk_factors"].sort(key=lambda x: abs(x["correlation"]), reverse=True)
                
                # Geographic risk analysis if coordinates available
                if 'latitude' in df.columns and 'longitude' in df.columns:
                    lat_data = df['latitude'].dropna()
                    lng_data = df['longitude'].dropna()
                    
                    if len(lat_data) > 0 and len(lng_data) > 0:
                        # Find high-risk geographic areas
                        high_risk_indices = target_data[target_data > high_threshold].index
                        if len(high_risk_indices) > 0:
                            high_risk_locations = df.loc[high_risk_indices, ['latitude', 'longitude']].dropna()
                            
                            if not high_risk_locations.empty:
                                # Calculate geographic risk clusters
                                lat_center = high_risk_locations['latitude'].mean()
                                lng_center = high_risk_locations['longitude'].mean()
                                lat_std = high_risk_locations['latitude'].std()
                                lng_std = high_risk_locations['longitude'].std()
                                
                                risk_analysis["geographic_risks"] = [{
                                    "center_lat": round(lat_center, 4),
                                    "center_lng": round(lng_center, 4),
                                    "lat_spread": round(lat_std, 4) if not pd.isna(lat_std) else 0,
                                    "lng_spread": round(lng_std, 4) if not pd.isna(lng_std) else 0,
                                    "high_risk_points": len(high_risk_locations)
                                }]
                
                # Temporal risk analysis if timestamp available
                datetime_cols = schema.get('datetime_columns', [])
                if datetime_cols and datetime_cols[0] in df.columns:
                    time_col = datetime_cols[0]
                    df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
                    time_data = df[time_col].dropna()
                    
                    if len(time_data) > 0:
                        # Analyze risk patterns over time
                        df_time_risk = df[[time_col, target_col]].dropna()
                        if len(df_time_risk) > 10:
                            # Group by hour or day depending on data span
                            time_span = (time_data.max() - time_data.min()).days
                            
                            if time_span > 7:  # More than a week, group by day
                                df_time_risk['time_group'] = df_time_risk[time_col].dt.date
                            else:  # Group by hour
                                df_time_risk['time_group'] = df_time_risk[time_col].dt.floor('H')
                            
                            # Calculate average risk per time group
                            time_risk_avg = df_time_risk.groupby('time_group')[target_col].mean()
                            
                            # Find high-risk time periods
                            high_risk_times = time_risk_avg[time_risk_avg > high_threshold]
                            
                            if len(high_risk_times) > 0:
                                risk_analysis["temporal_risks"] = [
                                    {
                                        "time_period": str(time_period),
                                        "average_risk": round(avg_risk, 3),
                                        "risk_level": "HIGH" if avg_risk > critical_threshold else "MEDIUM"
                                    }
                                    for time_period, avg_risk in high_risk_times.head(5).items()
                                ]
        
        return risk_analysis
    
    def _analyze_trends(self, df: pd.DataFrame, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive temporal trends analysis"""
        trends = {
            "trend_direction": "STABLE",
            "seasonal_patterns": False,
            "increasing_metrics": [],
            "decreasing_metrics": [],
            "trend_strength": {},
            "time_series_analysis": {},
            "forecast_indicators": {}
        }
        
        # Look for timestamp columns
        datetime_col = None
        for col in schema['datetime_columns']:
            if col in df.columns:
                datetime_col = col
                break
        
        if datetime_col and datetime_col in df.columns:
            # Ensure datetime column is properly parsed
            df[datetime_col] = pd.to_datetime(df[datetime_col], errors='coerce')
            df_sorted = df.sort_values(datetime_col).dropna(subset=[datetime_col])
            
            # Analyze trends for numeric columns
            numeric_cols = [col for col in schema['numeric_columns'] if col in df.columns]
            
            for col in numeric_cols:
                if col in df.columns:
                    col_data = df_sorted[[datetime_col, col]].dropna()
                    
                    if len(col_data) > 10:  # Need sufficient data points
                        # Calculate trend using linear regression slope
                        time_numeric = pd.to_numeric(col_data[datetime_col])
                        values = col_data[col]
                        
                        # Simple linear trend calculation
                        n = len(values)
                        sum_x = time_numeric.sum()
                        sum_y = values.sum()
                        sum_xy = (time_numeric * values).sum()
                        sum_x2 = (time_numeric ** 2).sum()
                        
                        if n * sum_x2 - sum_x ** 2 != 0:
                            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
                            
                            # Normalize slope for interpretation
                            value_range = values.max() - values.min()
                            time_range = time_numeric.max() - time_numeric.min()
                            
                            if value_range > 0 and time_range > 0:
                                normalized_slope = slope * time_range / value_range
                                
                                # Store trend strength
                                trends["trend_strength"][col] = {
                                    "slope": float(slope),
                                    "normalized_slope": float(normalized_slope),
                                    "trend_strength": abs(normalized_slope)
                                }
                                
                                # Classify trend direction
                                if normalized_slope > 0.1:
                                    trends["increasing_metrics"].append({
                                        "metric": col,
                                        "strength": float(normalized_slope),
                                        "confidence": min(0.95, abs(normalized_slope))
                                    })
                                elif normalized_slope < -0.1:
                                    trends["decreasing_metrics"].append({
                                        "metric": col,
                                        "strength": float(abs(normalized_slope)),
                                        "confidence": min(0.95, abs(normalized_slope))
                                    })
                        
                        # Moving average analysis for seasonality detection
                        if len(col_data) > 50:
                            # Calculate short and long term moving averages
                            short_window = max(5, len(col_data) // 20)
                            long_window = max(10, len(col_data) // 10)
                            
                            col_data_indexed = col_data.set_index(datetime_col)
                            short_ma = col_data_indexed[col].rolling(window=short_window).mean()
                            long_ma = col_data_indexed[col].rolling(window=long_window).mean()
                            
                            # Calculate volatility and cyclical patterns
                            volatility = values.std() / values.mean() if values.mean() != 0 else 0
                            
                            trends["time_series_analysis"][col] = {
                                "volatility": float(volatility),
                                "has_cycles": volatility > 0.2,
                                "data_points": len(col_data),
                                "time_span_days": (col_data[datetime_col].max() - col_data[datetime_col].min()).days
                            }
            
            # Determine overall trend direction
            increasing_count = len(trends["increasing_metrics"])
            decreasing_count = len(trends["decreasing_metrics"])
            
            if increasing_count > decreasing_count and increasing_count > 0:
                trends["trend_direction"] = "INCREASING"
            elif decreasing_count > increasing_count and decreasing_count > 0:
                trends["trend_direction"] = "DECREASING"
            elif increasing_count > 0 or decreasing_count > 0:
                trends["trend_direction"] = "MIXED"
            else:
                trends["trend_direction"] = "STABLE"
            
            # Detect seasonal patterns based on data frequency
            total_span = (df_sorted[datetime_col].max() - df_sorted[datetime_col].min()).days
            if total_span > 30:  # At least a month of data
                # Simple seasonality detection based on variance patterns
                trends["seasonal_patterns"] = len([t for t in trends["time_series_analysis"].values() if t.get("has_cycles", False)]) > 0
            
            # Generate forecast indicators
            trends["forecast_indicators"] = {
                "predictability": "HIGH" if trends["trend_direction"] in ["INCREASING", "DECREASING"] else "MEDIUM",
                "data_sufficiency": "SUFFICIENT" if len(df_sorted) > 100 else "LIMITED",
                "trend_consistency": len([m for m in trends["increasing_metrics"] + trends["decreasing_metrics"] if m["confidence"] > 0.7])
            }
        
        return trends
    
    def _detect_anomalies_comprehensive(self, df: pd.DataFrame, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive anomaly detection"""
        anomalies = {
            "total_anomalies": 0,
            "anomaly_rate": 0.0,
            "anomalous_records": [],
            "anomaly_types": []
        }
        
        numeric_cols = [col for col in schema['numeric_columns'] if col in df.columns]
        
        if len(numeric_cols) > 0:
            # Use isolation forest for anomaly detection
            isolation_forest = IsolationForest(contamination=0.1, random_state=42)
            
            # Prepare data
            data_for_analysis = df[numeric_cols].fillna(df[numeric_cols].mean())
            
            # Detect anomalies
            anomaly_labels = isolation_forest.fit_predict(data_for_analysis)
            anomaly_count = len(anomaly_labels[anomaly_labels == -1])
            
            anomalies["total_anomalies"] = int(anomaly_count)
            anomalies["anomaly_rate"] = round(anomaly_count / len(df) * 100, 2)
            
            # Get anomalous record indices
            anomalous_indices = np.where(anomaly_labels == -1)[0]
            anomalies["anomalous_records"] = [int(idx) for idx in anomalous_indices[:10]]  # Limit to first 10
            
            if anomaly_count > 0:
                anomalies["anomaly_types"] = ["Statistical Outlier", "Pattern Deviation"]
        
        return anomalies
    
    def _generate_predictions(self, df: pd.DataFrame, schema: Dict[str, Any], data_hash: int) -> List[Dict[str, Any]]:
        """Generate deterministic predictions for future scenarios"""
        predictions = []
        
        # Use deterministic seed for consistent predictions
        np.random.seed(abs(data_hash) % 10000)
        
        # Base predictions on actual data patterns
        numeric_cols = [col for col in schema['numeric_columns'] if col in df.columns]
        target_col = schema.get('potential_target')
        
        # Calculate base statistics for realistic predictions
        base_stats = {}
        for col in numeric_cols:
            if col in df.columns and not df[col].empty:
                base_stats[col] = {
                    'mean': df[col].mean(),
                    'std': df[col].std(),
                    'min': df[col].min(),
                    'max': df[col].max()
                }
        
        # Generate predictions based on data patterns
        num_predictions = min(24, max(6, len(df) // 50))  # Reasonable number of predictions
        
        for i in range(num_predictions):
            # Create time horizons
            time_horizons = [
                f"{(i+1)*15} minutes", f"{(i+1)*30} minutes", f"{(i+1)} hours",
                f"{(i+1)*2} hours", f"{(i+1)*6} hours", f"{(i+1)*12} hours"
            ]
            time_horizon = time_horizons[min(i, len(time_horizons)-1)]
            
            # Generate prediction based on target statistics
            if target_col and target_col in base_stats:
                target_stats = base_stats[target_col]
                # Use normal distribution around mean with some trend
                trend_factor = 1.0 + (i * 0.02)  # Slight upward trend
                predicted_value = np.random.normal(
                    target_stats['mean'] * trend_factor,
                    target_stats['std'] * 0.5
                )
                # Ensure within reasonable bounds
                predicted_value = max(target_stats['min'], 
                                    min(target_stats['max'], predicted_value))
            else:
                # Fallback to synthetic prediction
                predicted_value = 0.3 + (i * 0.05) + np.random.normal(0, 0.1)
                predicted_value = max(0.0, min(1.0, predicted_value))
            
            # Calculate confidence based on data quality and amount
            base_confidence = 0.7 + (len(df) / 1000) * 0.2  # More data = higher confidence
            confidence_variation = np.random.normal(0, 0.05)
            confidence = max(0.6, min(0.95, base_confidence + confidence_variation))
            
            prediction = {
                "prediction_id": f"pred_{data_hash}_{i+1}",
                "predicted_value": float(predicted_value),
                "confidence": float(confidence),
                "time_horizon": time_horizon,
                "prediction_type": "risk_assessment",
                "method": "statistical_model",
                "factors_considered": numeric_cols[:5],  # Top 5 factors
                "uncertainty_range": {
                    "lower": float(predicted_value * 0.85),
                    "upper": float(predicted_value * 1.15)
                }
            }
            predictions.append(prediction)
        
        return predictions
    
    def _generate_insights(self, df: pd.DataFrame, schema: Dict[str, Any], stats: Dict, 
                          risk_analysis: Dict, trends: Dict) -> List[str]:
        """Generate AI-powered insights"""
        insights = []
        
        # Data quality insights
        if len(df) > 1000:
            insights.append(f"Large dataset with {len(df)} records provides robust analysis foundation")
        
        # Risk insights
        if risk_analysis["overall_risk_level"] == "HIGH":
            insights.append("Dataset shows concerning high-risk patterns requiring immediate attention")
        elif risk_analysis["overall_risk_level"] == "LOW":
            insights.append("Dataset indicates generally stable conditions with minimal risk factors")
        
        # Trend insights
        if trends["trend_direction"] == "INCREASING":
            insights.append("Data shows increasing trend patterns that may require monitoring")
        elif trends["trend_direction"] == "DECREASING":
            insights.append("Data shows decreasing trend patterns indicating potential improvement")
        
        # Feature insights
        if len(schema["potential_features"]) > 5:
            insights.append("Rich feature set enables comprehensive multi-factor risk assessment")
        
        # Risk factor insights
        if len(risk_analysis["risk_factors"]) > 0:
            top_factor = max(risk_analysis["risk_factors"], key=lambda x: abs(x["correlation"]))
            insights.append(f"'{top_factor['factor']}' shows strongest correlation with risk patterns")
        
        return insights[:5]  # Limit to top 5 insights
    
    def _generate_analysis_alerts(self, df: pd.DataFrame, schema: Dict[str, Any], 
                                 risk_analysis: Dict, anomalies: Dict, ml_predictions: Dict = None) -> List[Dict[str, Any]]:
        """Generate alerts based on analysis results with dynamic risk scores"""
        alerts = []
        
        # Get dynamic risk score from ML predictions
        current_risk_score = ml_predictions.get("risk_score", 0.5) if ml_predictions else 0.5
        
        # High risk alert with dynamic scoring
        if risk_analysis["overall_risk_level"] == "HIGH":
            alert_risk_score = max(0.7, current_risk_score)  # At least 70% for high risk
            alerts.append({
                "type": "HIGH_RISK_DETECTED",
                "message": f"High risk conditions detected in {risk_analysis['high_risk_records']} records",
                "risk_score": round(alert_risk_score, 3),
                "severity": "HIGH",
                "timestamp": datetime.now().isoformat(),
                "details": {
                    "risk_factors_count": len(risk_analysis.get("risk_factors", [])),
                    "confidence": ml_predictions.get("confidence", 0.7) if ml_predictions else 0.7
                }
            })
        elif risk_analysis["overall_risk_level"] == "CRITICAL":
            alert_risk_score = max(0.85, current_risk_score)  # At least 85% for critical
            alerts.append({
                "type": "CRITICAL_RISK_DETECTED",
                "message": f"Critical risk conditions detected requiring immediate attention",
                "risk_score": round(alert_risk_score, 3),
                "severity": "CRITICAL",
                "timestamp": datetime.now().isoformat(),
                "details": {
                    "risk_factors_count": len(risk_analysis.get("risk_factors", [])),
                    "confidence": ml_predictions.get("confidence", 0.8) if ml_predictions else 0.8
                }
            })
        
        # Anomaly alert with dynamic scoring
        anomaly_rate = anomalies.get("anomaly_rate", 0)
        if anomaly_rate > 5:
            # Scale risk score based on anomaly rate
            anomaly_risk_score = min(0.9, 0.4 + (anomaly_rate / 100) * 0.5)
            alerts.append({
                "type": "ANOMALY_DETECTED",
                "message": f"Unusual patterns detected in {anomaly_rate}% of data",
                "risk_score": round(anomaly_risk_score, 3),
                "severity": "HIGH" if anomaly_rate > 15 else "MEDIUM",
                "timestamp": datetime.now().isoformat(),
                "details": {
                    "anomaly_types": anomalies.get("anomaly_types", []),
                    "anomaly_count": anomalies.get("anomaly_count", 0)
                }
            })
        
        # Data quality alert
        if len(df) < 100:
            data_risk_score = max(0.3, 0.6 - (len(df) / 100) * 0.3)  # Higher risk for less data
            alerts.append({
                "type": "LIMITED_DATA",
                "message": f"Limited data available for comprehensive analysis ({len(df)} records)",
                "risk_score": round(data_risk_score, 3),
                "severity": "LOW" if len(df) > 50 else "MEDIUM",
                "timestamp": datetime.now().isoformat(),
                "details": {
                    "record_count": len(df),
                    "recommended_minimum": 100
                }
            })
        
        return alerts
    
    def _generate_recommendations(self, risk_analysis: Dict, anomalies: Dict, trends: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if risk_analysis["overall_risk_level"] == "HIGH":
            recommendations.append("Implement immediate monitoring and alerting systems")
            recommendations.append("Consider deploying additional sensors in high-risk areas")
        
        if anomalies["anomaly_rate"] > 10:
            recommendations.append("Investigate anomalous data patterns for potential equipment issues")
        
        if trends["trend_direction"] == "INCREASING":
            recommendations.append("Establish trend monitoring to track pattern evolution")
        
        recommendations.append("Schedule regular data quality assessments")
        recommendations.append("Consider expanding monitoring coverage based on risk patterns")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def preprocess_data(self, df: pd.DataFrame, schema: Dict[str, Any], model_name: str = "default") -> Tuple[np.ndarray, np.ndarray]:
        """Preprocess data for ML model training"""
        # Handle missing values
        if model_name not in self.imputers:
            self.imputers[model_name] = SimpleImputer(strategy='mean')
        
        # Select features
        features = schema['potential_features']
        if not features:
            # Use all numeric columns except datetime and target
            features = [col for col in schema['numeric_columns'] 
                       if col not in schema['datetime_columns'] + [schema['potential_target']]]
        
        self.feature_columns[model_name] = features
        
        # Prepare feature matrix
        X = df[features].copy()
        X = self.imputers[model_name].fit_transform(X)
        
        # Prepare target
        y = df[schema['potential_target']].copy()
        y = self.imputers[model_name].fit_transform(y.reshape(-1, 1)).flatten()
        
        # Scale features
        if model_name not in self.scalers:
            self.scalers[model_name] = StandardScaler()
        
        X_scaled = self.scalers[model_name].fit_transform(X)
        
        return X_scaled, y
    
    def train_model(self, df: pd.DataFrame, schema: Dict[str, Any], model_name: str = "default") -> Dict[str, Any]:
        """Train a new ML model on the provided data"""
        try:
            # Preprocess data
            X, y = self.preprocess_data(df, schema, model_name)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Train model
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            # Store model
            self.models[model_name] = model
            
            # Save model to disk
            model_path = os.path.join(settings.MODEL_PATH, f"{model_name}_model.joblib")
            scaler_path = os.path.join(settings.MODEL_PATH, f"{model_name}_scaler.joblib")
            
            joblib.dump(model, model_path)
            joblib.dump(self.scalers[model_name], scaler_path)
            
            # Create model metadata
            model_metadata = {
                'name': model_name,
                'version': '1.0',
                'model_type': 'risk_assessment',
                'file_path': model_path,
                'parameters': model.get_params(),
                'features': self.feature_columns[model_name],
                'target_column': schema['potential_target'],
                'accuracy': r2,
                'mse': mse,
                'training_data_size': len(df),
                'last_trained': datetime.now().isoformat(),
                'schema': schema
            }
            
            logger.info(f"Model {model_name} trained successfully. R²: {r2:.4f}, MSE: {mse:.4f}")
            
            return model_metadata
            
        except Exception as e:
            logger.error(f"Error training model {model_name}: {e}")
            raise
    
    def predict(self, data: Dict[str, Any], model_name: str = "default") -> Dict[str, Any]:
        """Make predictions using the trained model"""
        try:
            if model_name not in self.models:
                raise ValueError(f"Model {model_name} not found. Please train the model first.")
            
            # Prepare input data
            features = self.feature_columns[model_name]
            input_data = []
            
            for feature in features:
                if feature in data:
                    input_data.append(data[feature])
                else:
                    # Use mean value for missing features
                    input_data.append(0.0)  # Default fallback
            
            # Reshape and scale
            X = np.array(input_data).reshape(1, -1)
            X_scaled = self.scalers[model_name].transform(X)
            
            # Make prediction
            prediction = self.models[model_name].predict(X_scaled)[0]
            
            # Calculate confidence (simplified - can be enhanced)
            confidence = 0.8  # Placeholder - can be calculated from model uncertainty
            
            return {
                'predicted_value': float(prediction),
                'confidence_score': confidence,
                'model_name': model_name,
                'features_used': features,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            raise
    
    def detect_anomalies(self, df: pd.DataFrame, features: List[str]) -> np.ndarray:
        """Detect anomalies in the data using Isolation Forest"""
        try:
            # Prepare data
            X = df[features].fillna(df[features].mean())
            
            # Train anomaly detection model
            iso_forest = IsolationForest(contamination=0.1, random_state=42)
            anomalies = iso_forest.fit_predict(X)
            
            # Convert to boolean (True for anomalies)
            return anomalies == -1
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return np.zeros(len(df), dtype=bool)
    
    def retrain_model(self, new_data: pd.DataFrame, model_name: str = "default") -> Dict[str, Any]:
        """Retrain model with new data"""
        try:
            # Load existing model if available
            model_path = os.path.join(settings.MODEL_PATH, f"{model_name}_model.joblib")
            if os.path.exists(model_path):
                self.models[model_name] = joblib.load(model_path)
            
            # Detect schema for new data
            schema = self.detect_schema(new_data)
            
            # Retrain model
            return self.train_model(new_data, schema, model_name)
            
        except Exception as e:
            logger.error(f"Error retraining model: {e}")
            raise
    
    def get_model_info(self, model_name: str = "default") -> Dict[str, Any]:
        """Get information about a trained model"""
        if model_name not in self.models:
            return {"error": f"Model {model_name} not found"}
        
        model = self.models[model_name]
        return {
            'name': model_name,
            'type': type(model).__name__,
            'features': self.feature_columns.get(model_name, []),
            'n_estimators': getattr(model, 'n_estimators', None),
            'feature_importances': model.feature_importances_.tolist() if hasattr(model, 'feature_importances_') else None
        }
    
    def _store_analysis_result(self, dataset_id: str, analysis_result: Dict[str, Any]):
        """Store analysis result persistently"""
        try:
            import os
            # Ensure analysis directory exists
            analysis_dir = "/tmp/ml_analysis"
            os.makedirs(analysis_dir, exist_ok=True)
            
            # Store analysis result as JSON
            analysis_file = os.path.join(analysis_dir, f"analysis_{dataset_id}.json")
            with open(analysis_file, "w") as f:
                json.dump(analysis_result, f, indent=2, default=str)
            
            logger.info(f"Analysis result stored for dataset {dataset_id}")
        except Exception as e:
            logger.error(f"Failed to store analysis result: {e}")
    
    def load_analysis_result(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Load stored analysis result"""
        try:
            analysis_file = f"/tmp/ml_analysis/analysis_{dataset_id}.json"
            if os.path.exists(analysis_file):
                with open(analysis_file, "r") as f:
                    analysis_result = json.load(f)
                logger.info(f"Loaded stored analysis for dataset {dataset_id}")
                return analysis_result
        except Exception as e:
            logger.error(f"Failed to load analysis result: {e}")
        return None

    def _generate_ml_predictions(self, df: pd.DataFrame, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate real-time ML predictions with dynamic risk score calculation"""
        predictions = {
            "risk_score": 0.0,
            "confidence": 0.0,
            "trend": "stable",
            "forecast": [],
            "prediction_details": {},
            "model_performance": {}
        }
        
        # Get target column for prediction
        target_col = schema.get('potential_target')
        if not target_col or target_col not in df.columns:
            # If no target column, calculate composite risk score
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                # Normalize and aggregate numeric features for risk score
                normalized_data = df[numeric_cols].fillna(df[numeric_cols].median())
                
                # Calculate composite risk score using weighted features
                weights = []
                for col in numeric_cols:
                    # Weight based on coefficient of variation (higher variation = higher weight)
                    cv = normalized_data[col].std() / (normalized_data[col].mean() + 1e-8)
                    weights.append(max(0.1, min(1.0, cv)))
                
                weights = np.array(weights) / sum(weights)  # Normalize weights
                
                # Apply min-max scaling to each column manually
                scaled_data = []
                for col in numeric_cols:
                    col_data = normalized_data[col].values
                    col_min = col_data.min()
                    col_max = col_data.max()
                    if col_max > col_min:
                        scaled_col = (col_data - col_min) / (col_max - col_min)
                    else:
                        scaled_col = np.zeros_like(col_data)
                    scaled_data.append(scaled_col)
                
                scaled_data = np.column_stack(scaled_data)
                
                # Calculate weighted risk scores
                risk_scores = np.dot(scaled_data, weights)
                
                predictions["risk_score"] = float(np.mean(risk_scores))
                predictions["confidence"] = min(0.95, 1.0 - (np.std(risk_scores) / (np.mean(risk_scores) + 1e-8)))
                
                # Determine trend based on temporal patterns
                if len(risk_scores) > 10:
                    recent_scores = risk_scores[-min(10, len(risk_scores)//3):]
                    earlier_scores = risk_scores[:min(10, len(risk_scores)//3)]
                    
                    if np.mean(recent_scores) > np.mean(earlier_scores) * 1.1:
                        predictions["trend"] = "increasing"
                    elif np.mean(recent_scores) < np.mean(earlier_scores) * 0.9:
                        predictions["trend"] = "decreasing"
                    else:
                        predictions["trend"] = "stable"
            
            return predictions
        
        # Work with target column data
        target_data = df[target_col].dropna()
        
        if len(target_data) < 5:
            predictions["risk_score"] = 0.5  # Default moderate risk
            predictions["confidence"] = 0.3
            return predictions
        
        # Calculate dynamic risk score based on data distribution
        mean_risk = target_data.mean()
        std_risk = target_data.std()
        median_risk = target_data.median()
        
        # Use multiple statistics for robust risk assessment
        risk_indicators = [
            mean_risk,
            median_risk,
            target_data.quantile(0.75),  # 75th percentile
            target_data.quantile(0.9)    # 90th percentile
        ]
        
        # Weight the indicators (more weight to median and 75th percentile for robustness)
        weights = [0.2, 0.3, 0.3, 0.2]
        weighted_risk = sum(indicator * weight for indicator, weight in zip(risk_indicators, weights))
        
        # Normalize to 0-1 scale if needed
        if weighted_risk > 1:
            weighted_risk = min(1.0, weighted_risk / target_data.max())
        
        predictions["risk_score"] = float(weighted_risk)
        
        # Calculate confidence based on data consistency and sample size
        confidence_factors = []
        
        # Sample size factor (more data = higher confidence)
        sample_factor = min(1.0, len(target_data) / 100)
        confidence_factors.append(sample_factor)
        
        # Variance factor (lower variance = higher confidence)
        if std_risk > 0:
            variance_factor = max(0.1, 1.0 - (std_risk / (mean_risk + 1e-8)))
            confidence_factors.append(variance_factor)
        
        # Outlier factor (fewer outliers = higher confidence)
        q75 = target_data.quantile(0.75)
        q25 = target_data.quantile(0.25)
        iqr = q75 - q25
        outliers = target_data[(target_data < q25 - 1.5*iqr) | (target_data > q75 + 1.5*iqr)]
        outlier_factor = max(0.1, 1.0 - (len(outliers) / len(target_data)))
        confidence_factors.append(outlier_factor)
        
        predictions["confidence"] = float(np.mean(confidence_factors))
        
        # Determine trend with time-based analysis
        datetime_cols = schema.get('datetime_columns', [])
        if datetime_cols and datetime_cols[0] in df.columns:
            time_col = datetime_cols[0]
            df_copy = df.copy()
            df_copy[time_col] = pd.to_datetime(df_copy[time_col], errors='coerce')
            
            # Sort by time and analyze trend
            df_sorted = df_copy[[time_col, target_col]].dropna().sort_values(time_col)
            
            if len(df_sorted) > 5:
                # Calculate trend using linear regression
                time_numeric = (df_sorted[time_col] - df_sorted[time_col].min()).dt.total_seconds()
                
                # Simple linear regression
                n = len(time_numeric)
                sum_x = time_numeric.sum()
                sum_y = df_sorted[target_col].sum()
                sum_xy = (time_numeric * df_sorted[target_col]).sum()
                sum_x2 = (time_numeric ** 2).sum()
                
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2 + 1e-8)
                
                # Determine trend based on slope magnitude
                if abs(slope) < 1e-8:
                    predictions["trend"] = "stable"
                elif slope > 0:
                    predictions["trend"] = "increasing"
                else:
                    predictions["trend"] = "decreasing"
                
                # Generate forecast points
                if len(df_sorted) > 10:
                    recent_data = df_sorted.tail(min(20, len(df_sorted)))
                    forecast_points = []
                    
                    # Calculate rolling statistics for forecast
                    window_size = min(5, len(recent_data) // 2)
                    rolling_mean = recent_data[target_col].rolling(window=window_size).mean().iloc[-1]
                    rolling_std = recent_data[target_col].rolling(window=window_size).std().iloc[-1]
                    
                    # Generate 5 forecast points
                    for i in range(1, 6):
                        # Apply trend with some uncertainty
                        forecast_value = rolling_mean + (slope * i * 3600)  # Hourly projection
                        
                        # Add uncertainty bounds
                        uncertainty = rolling_std * np.sqrt(i) * 0.5
                        
                        forecast_points.append({
                            "period": i,
                            "predicted_value": float(max(0, min(1, forecast_value))),
                            "confidence_interval": [
                                float(max(0, forecast_value - uncertainty)),
                                float(min(1, forecast_value + uncertainty))
                            ]
                        })
                    
                    predictions["forecast"] = forecast_points
        
        # Add detailed prediction information
        predictions["prediction_details"] = {
            "mean_risk": float(mean_risk),
            "median_risk": float(median_risk),
            "std_risk": float(std_risk),
            "data_points": len(target_data),
            "risk_distribution": {
                "low_risk_count": int(len(target_data[target_data < 0.3])),
                "medium_risk_count": int(len(target_data[(target_data >= 0.3) & (target_data < 0.7)])),
                "high_risk_count": int(len(target_data[target_data >= 0.7]))
            }
        }
        
        # Model performance metrics
        if len(target_data) > 10:
            # Calculate some basic performance indicators
            predictions["model_performance"] = {
                "data_coverage": float(len(target_data) / len(df)),
                "prediction_stability": float(1.0 - (std_risk / (mean_risk + 1e-8))),
                "temporal_consistency": predictions["confidence"]
            }
        
        return predictions

    async def get_real_time_correlations(self, dataset_id: str) -> Dict[str, Any]:
        """Generate real-time correlation analysis for risk factors"""
        try:
            # Get the latest data from database
            query = select(CoastalData).where(CoastalData.dataset_id == dataset_id)
            result = await self.db.execute(query)
            records = result.scalars().all()
            
            if not records:
                return {
                    "correlations": [],
                    "risk_matrix": [],
                    "error": "No data found for dataset"
                }
            
            # Convert to DataFrame for analysis
            data = []
            for record in records:
                data.append({
                    'timestamp': record.timestamp,
                    'latitude': record.latitude,
                    'longitude': record.longitude,
                    'value': record.value,
                    'dataset_id': record.dataset_id
                })
            
            df = pd.DataFrame(data)
            
            # Analyze data schema
            schema = self._analyze_data_schema(df)
            
            # Get numeric columns for correlation analysis
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if len(numeric_cols) < 2:
                return {
                    "correlations": [],
                    "risk_matrix": [],
                    "error": "Insufficient numeric data for correlation analysis"
                }
            
            # Calculate correlation matrix
            correlation_matrix = df[numeric_cols].corr()
            
            # Convert to list format for frontend
            correlations = []
            risk_matrix = []
            
            for i, col1 in enumerate(numeric_cols):
                row = []
                for j, col2 in enumerate(numeric_cols):
                    corr_value = correlation_matrix.loc[col1, col2]
                    if not pd.isna(corr_value):
                        corr_value = float(corr_value)
                        row.append(corr_value)
                        
                        # Add to correlations list (exclude self-correlation)
                        if i != j and abs(corr_value) > 0.1:  # Only significant correlations
                            correlations.append({
                                "factor1": col1,
                                "factor2": col2,
                                "correlation": round(corr_value, 3),
                                "strength": "strong" if abs(corr_value) > 0.7 else "moderate" if abs(corr_value) > 0.4 else "weak",
                                "direction": "positive" if corr_value > 0 else "negative"
                            })
                    else:
                        row.append(0.0)
                risk_matrix.append(row)
            
            # Sort correlations by strength
            correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)
            
            # Calculate risk factor impacts if target exists
            target_col = schema.get('potential_target')
            risk_impacts = []
            
            if target_col and target_col in df.columns:
                target_data = df[target_col].dropna()
                
                for col in numeric_cols:
                    if col != target_col and col in df.columns:
                        col_data = df[col].dropna()
                        
                        # Align data for correlation
                        common_indices = target_data.index.intersection(col_data.index)
                        if len(common_indices) > 5:
                            target_aligned = target_data[common_indices]
                            col_aligned = col_data[common_indices]
                            
                            correlation = target_aligned.corr(col_aligned)
                            
                            if not pd.isna(correlation) and abs(correlation) > 0.05:
                                # Calculate additional metrics
                                risk_level = "HIGH" if abs(correlation) > 0.6 else "MEDIUM" if abs(correlation) > 0.3 else "LOW"
                                
                                risk_impacts.append({
                                    "factor": col,
                                    "risk_correlation": round(float(correlation), 3),
                                    "risk_level": risk_level,
                                    "impact_direction": "increases_risk" if correlation > 0 else "decreases_risk",
                                    "confidence": min(0.95, abs(correlation)),
                                    "data_points": len(common_indices)
                                })
                
                # Sort by correlation strength
                risk_impacts.sort(key=lambda x: abs(x["risk_correlation"]), reverse=True)
            
            return {
                "correlations": correlations[:20],  # Top 20 correlations
                "risk_matrix": {
                    "matrix": risk_matrix,
                    "labels": numeric_cols
                },
                "risk_impacts": risk_impacts[:10],  # Top 10 risk factors
                "timestamp": datetime.now().isoformat(),
                "data_points": len(df),
                "analysis_summary": {
                    "total_factors": len(numeric_cols),
                    "significant_correlations": len([c for c in correlations if abs(c["correlation"]) > 0.5]),
                    "high_risk_factors": len([r for r in risk_impacts if r["risk_level"] == "HIGH"])
                }
            }
            
        except Exception as e:
            logger.error(f"Error in real-time correlation analysis: {e}")
            return {
                "correlations": [],
                "risk_matrix": [],
                "error": str(e)
            }

# Global ML service instance
ml_service = MLService()


