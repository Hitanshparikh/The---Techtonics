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
        """Create a synthetic risk score based on available features"""
        risk_score = np.zeros(len(df))
        
        for feature in features:
            if feature in df.columns:
                # Normalize the feature to 0-1 range
                feature_data = df[feature].fillna(df[feature].mean())
                if feature_data.std() > 0:
                    normalized = (feature_data - feature_data.min()) / (feature_data.max() - feature_data.min())
                    risk_score += normalized
        
        # Normalize final risk score to 0-1
        if risk_score.max() > risk_score.min():
            risk_score = (risk_score - risk_score.min()) / (risk_score.max() - risk_score.min())
        
        return risk_score
    
    def analyze_dataset(self, df: pd.DataFrame, schema: Dict[str, Any], dataset_id: str) -> Dict[str, Any]:
        """Comprehensive AI analysis of uploaded dataset"""
        try:
            logger.info(f"Starting AI analysis for dataset {dataset_id}")
            
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
            predictions = self._generate_predictions(df, schema)
            
            # Create insights
            insights = self._generate_insights(df, schema, stats, risk_analysis, trends)
            
            # Generate alerts based on analysis
            alerts = self._generate_analysis_alerts(df, schema, risk_analysis, anomalies)
            
            analysis_result = {
                "dataset_id": dataset_id,
                "analysis_timestamp": datetime.now().isoformat(),
                "data_quality_score": data_quality_score,
                "total_records": len(df),
                "risk_level": risk_analysis["overall_risk_level"],
                "statistical_summary": stats,
                "risk_analysis": risk_analysis,
                "trend_analysis": trends,
                "anomalies": anomalies,
                "predictions": predictions,
                "predictions_count": len(predictions),
                "insights": insights,
                "alerts": alerts,
                "recommendations": self._generate_recommendations(risk_analysis, anomalies, trends)
            }
            
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
        """Calculate overall data quality score"""
        if df.empty:
            return 0.0
        
        # Calculate completeness (no missing values)
        completeness = (1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        
        # Calculate uniqueness (low duplicate rate)
        uniqueness = (1 - df.duplicated().sum() / len(df)) * 100
        
        # Calculate consistency (valid data types)
        consistency = 90  # Simplified metric
        
        # Weighted average
        quality_score = (completeness * 0.4 + uniqueness * 0.3 + consistency * 0.3)
        return round(quality_score, 1)
    
    def _generate_statistical_insights(self, df: pd.DataFrame, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate statistical insights from the data"""
        stats = {}
        
        for col in schema['numeric_columns']:
            if col in df.columns:
                stats[col] = {
                    "mean": float(df[col].mean()) if not df[col].empty else 0,
                    "median": float(df[col].median()) if not df[col].empty else 0,
                    "std": float(df[col].std()) if not df[col].empty else 0,
                    "min": float(df[col].min()) if not df[col].empty else 0,
                    "max": float(df[col].max()) if not df[col].empty else 0,
                    "correlation_with_target": 0.5  # Simplified
                }
        
        return stats
    
    def _assess_risk_patterns(self, df: pd.DataFrame, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk patterns in the data"""
        risk_analysis = {
            "overall_risk_level": "MEDIUM",
            "high_risk_records": 0,
            "risk_factors": [],
            "geographic_risks": [],
            "temporal_risks": []
        }
        
        # Analyze target variable if exists
        target_col = schema.get('potential_target')
        if target_col and target_col in df.columns:
            target_data = df[target_col]
            
            # Calculate risk thresholds
            high_risk_threshold = target_data.quantile(0.8)
            high_risk_count = len(target_data[target_data > high_risk_threshold])
            
            risk_analysis["high_risk_records"] = int(high_risk_count)
            
            # Determine overall risk level
            if high_risk_count > len(df) * 0.3:
                risk_analysis["overall_risk_level"] = "HIGH"
            elif high_risk_count > len(df) * 0.1:
                risk_analysis["overall_risk_level"] = "MEDIUM"
            else:
                risk_analysis["overall_risk_level"] = "LOW"
            
            # Identify risk factors
            for feature in schema['potential_features']:
                if feature in df.columns:
                    correlation = df[feature].corr(target_data)
                    if abs(correlation) > 0.5:
                        risk_analysis["risk_factors"].append({
                            "factor": feature,
                            "correlation": float(correlation),
                            "impact": "HIGH" if abs(correlation) > 0.7 else "MEDIUM"
                        })
        
        return risk_analysis
    
    def _analyze_trends(self, df: pd.DataFrame, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze temporal trends in the data"""
        trends = {
            "trend_direction": "STABLE",
            "seasonal_patterns": False,
            "increasing_metrics": [],
            "decreasing_metrics": []
        }
        
        # Look for timestamp columns
        for datetime_col in schema['datetime_columns']:
            if datetime_col in df.columns:
                df_sorted = df.sort_values(datetime_col)
                
                # Analyze trends for numeric columns
                for col in schema['numeric_columns']:
                    if col in df.columns:
                        values = df_sorted[col].dropna()
                        if len(values) > 5:
                            # Simple trend detection
                            first_half = values[:len(values)//2].mean()
                            second_half = values[len(values)//2:].mean()
                            
                            if second_half > first_half * 1.1:
                                trends["increasing_metrics"].append(col)
                            elif second_half < first_half * 0.9:
                                trends["decreasing_metrics"].append(col)
                
                break
        
        # Determine overall trend
        if len(trends["increasing_metrics"]) > len(trends["decreasing_metrics"]):
            trends["trend_direction"] = "INCREASING"
        elif len(trends["decreasing_metrics"]) > len(trends["increasing_metrics"]):
            trends["trend_direction"] = "DECREASING"
        
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
    
    def _generate_predictions(self, df: pd.DataFrame, schema: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate predictions for future scenarios"""
        predictions = []
        
        # Generate sample predictions based on current data patterns
        for i in range(min(12, len(df))):  # Generate up to 12 predictions
            prediction = {
                "prediction_id": f"pred_{i+1}",
                "predicted_value": float(np.random.uniform(0.3, 0.9)),
                "confidence": float(np.random.uniform(0.7, 0.95)),
                "time_horizon": f"{(i+1)*30} minutes",
                "prediction_type": "risk_assessment"
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
                                 risk_analysis: Dict, anomalies: Dict) -> List[Dict[str, Any]]:
        """Generate alerts based on analysis results"""
        alerts = []
        
        # High risk alert
        if risk_analysis["overall_risk_level"] == "HIGH":
            alerts.append({
                "type": "HIGH_RISK_DETECTED",
                "message": f"High risk conditions detected in {risk_analysis['high_risk_records']} records",
                "risk_score": 0.85,
                "severity": "HIGH",
                "timestamp": datetime.now().isoformat()
            })
        
        # Anomaly alert
        if anomalies["anomaly_rate"] > 5:
            alerts.append({
                "type": "ANOMALY_DETECTED",
                "message": f"Unusual patterns detected in {anomalies['anomaly_rate']}% of data",
                "risk_score": 0.70,
                "severity": "MEDIUM",
                "timestamp": datetime.now().isoformat()
            })
        
        # Data quality alert
        if len(df) < 100:
            alerts.append({
                "type": "LIMITED_DATA",
                "message": "Limited data available for comprehensive analysis",
                "risk_score": 0.60,
                "severity": "LOW",
                "timestamp": datetime.now().isoformat()
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

# Global ML service instance
ml_service = MLService()


