-- Initialize Coastal Threat Alert System Database
-- This script creates the database schema and populates it with sample data

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tables (if they don't exist)
-- Note: In production, these would be created by SQLAlchemy migrations

-- Sample data for demonstration
-- In production, this would be populated by the application

-- Insert sample coastal regions
INSERT INTO coastal_regions (id, name, description, bounds) VALUES
('mumbai', 'Mumbai', 'Mumbai coastal region including Marine Drive and Juhu Beach', 
 '{"lat_min": 18.9, "lat_max": 19.3, "lng_min": 72.7, "lng_max": 73.0}'),
('gujarat', 'Gujarat', 'Gujarat coastal region including Surat and Bhavnagar', 
 '{"lat_min": 20.0, "lat_max": 24.0, "lng_min": 68.0, "lng_max": 73.0}');

-- Insert sample contacts
INSERT INTO contacts (id, name, phone, email, region, preferences, is_active) VALUES
('1', 'Emergency Response', '+919876543210', 'emergency@coastal.gov', 'Mumbai', 
 '{"sms_enabled": true, "email_enabled": true}', true),
('2', 'Coastal Patrol', '+919876543211', 'patrol@coastal.gov', 'Gujarat', 
 '{"sms_enabled": true, "email_enabled": false}', true),
('3', 'Weather Station', '+919876543212', 'weather@coastal.gov', 'Mumbai', 
 '{"sms_enabled": false, "email_enabled": true}', true),
('4', 'Local Authority', '+919876543213', 'authority@coastal.gov', 'Gujarat', 
 '{"sms_enabled": true, "email_enabled": true}', true);

-- Insert sample alert subscriptions
INSERT INTO alert_subscriptions (id, contact_id, alert_type, severity_threshold, channels, is_active) VALUES
('1', '1', 'flood_warning', 0.7, '["sms", "email"]', true),
('2', '1', 'storm_alert', 0.8, '["sms", "email"]', true),
('3', '2', 'flood_warning', 0.6, '["sms"]', true),
('4', '3', 'tide_monitoring', 0.5, '["email"]', true),
('5', '4', 'anomaly_detection', 0.7, '["sms", "email"]', true);

-- Insert sample ML models
INSERT INTO ml_models (id, name, version, model_type, file_path, parameters, features, target_column, accuracy, training_data_size, last_trained, is_active) VALUES
('1', 'default', '1.0', 'risk_assessment', '/app/data/models/default_model.joblib', 
 '{"n_estimators": 100, "random_state": 42}', 
 '["tide_level", "wave_height", "wind_speed", "pressure", "temperature", "humidity"]', 
 'synthetic_risk_score', 0.85, 1000, '2024-01-01T10:00:00', true),
('2', 'mumbai_coastal', '1.2', 'anomaly_detection', '/app/data/models/mumbai_model.joblib', 
 '{"contamination": 0.1, "random_state": 42}', 
 '["tide_level", "wave_height", "wind_speed", "pressure"]', 
 'anomaly_score', 0.92, 2500, '2024-01-10T15:30:00', true);

-- Insert sample datasets
INSERT INTO datasets (id, name, description, source_type, source_url, file_path, schema, total_records, status) VALUES
('1', 'Mumbai Coastal Data', 'Historical coastal data for Mumbai region', 'file', NULL, 
 '/app/data/uploads/mumbai_coastal_data.csv', 
 '{"columns": ["timestamp", "latitude", "longitude", "tide_level", "wave_height", "wind_speed", "risk_score"], "total_records": 1500}', 
 1500, 'active'),
('2', 'Gujarat Weather API', 'Real-time weather data from Gujarat coast', 'api', 
 'https://api.weather.gov/gujarat/coastal', NULL, 
 '{"columns": ["timestamp", "latitude", "longitude", "temperature", "humidity", "pressure", "wind_speed"], "total_records": 2500}', 
 2500, 'active');

-- Insert sample coastal data
INSERT INTO coastal_data (id, dataset_id, timestamp, latitude, longitude, data_fields, risk_score, anomaly_detected) VALUES
('1', '1', '2024-01-01T10:00:00', 19.0760, 72.8777, 
 '{"tide_level": 2.5, "wave_height": 1.2, "wind_speed": 15.3, "temperature": 28.5, "humidity": 75}', 
 0.7, false),
('2', '1', '2024-01-01T10:15:00', 19.0760, 72.8777, 
 '{"tide_level": 2.8, "wave_height": 1.5, "wind_speed": 18.7, "temperature": 29.1, "humidity": 78}', 
 0.6, false),
('3', '2', '2024-01-01T10:00:00', 22.2587, 71.1924, 
 '{"temperature": 32.5, "humidity": 65, "pressure": 1008.5, "wind_speed": 22.1}', 
 0.8, true),
('4', '2', '2024-01-01T10:15:00', 22.2587, 71.1924, 
 '{"temperature": 33.2, "humidity": 62, "pressure": 1007.8, "wind_speed": 25.3}', 
 0.9, true);

-- Insert sample predictions
INSERT INTO predictions (id, model_id, coastal_data_id, predicted_value, confidence_score, prediction_type, input_features) VALUES
('1', '1', '1', 0.72, 0.85, 'risk_score', 
 '{"tide_level": 2.5, "wave_height": 1.2, "wind_speed": 15.3, "pressure": 1013.25, "temperature": 28.5, "humidity": 75}'),
('2', '1', '2', 0.68, 0.82, 'risk_score', 
 '{"tide_level": 2.8, "wave_height": 1.5, "wind_speed": 18.7, "pressure": 1012.8, "temperature": 29.1, "humidity": 78}'),
('3', '2', '3', 1.0, 0.95, 'anomaly', 
 '{"tide_level": 3.1, "wave_height": 2.8, "wind_speed": 22.1, "pressure": 1005.2}'),
('4', '2', '4', 1.0, 0.98, 'anomaly', 
 '{"tide_level": 3.5, "wave_height": 3.2, "wind_speed": 28.5, "pressure": 1002.1}');

-- Insert sample alerts
INSERT INTO alerts (id, contact_id, alert_type, severity, message, channel, status, risk_score, location_data, triggered_at, sent_at, delivery_attempts) VALUES
('1', '1', 'flood_warning', 'high', 'High tide levels detected in Mumbai region. Risk score: 0.8', 'sms', 'sent', 0.8, 
 '{"lat": 19.0760, "lng": 72.8777, "region": "Mumbai"}', '2024-01-01T10:00:00', '2024-01-01T10:01:00', 1),
('2', '2', 'storm_alert', 'critical', 'Severe storm approaching Gujarat coast. Risk score: 0.95', 'sms', 'sent', 0.95, 
 '{"lat": 22.2587, "lng": 71.1924, "region": "Gujarat"}', '2024-01-01T09:30:00', '2024-01-01T09:31:00', 1),
('3', '3', 'tide_monitoring', 'medium', 'Unusual tide patterns detected in Mumbai. Risk score: 0.6', 'email', 'failed', 0.6, 
 '{"lat": 19.0760, "lng": 72.8777, "region": "Mumbai"}', '2024-01-01T08:45:00', NULL, 3);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_coastal_data_timestamp ON coastal_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_coastal_data_location ON coastal_data(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_alerts_triggered_at ON alerts(triggered_at);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_contacts_region ON contacts(region);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO coastal_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO coastal_user;

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'Database initialization completed successfully';
    RAISE NOTICE 'Sample data inserted: % coastal data records, % contacts, % alerts', 
        (SELECT COUNT(*) FROM coastal_data),
        (SELECT COUNT(*) FROM contacts),
        (SELECT COUNT(*) FROM alerts);
END $$;


