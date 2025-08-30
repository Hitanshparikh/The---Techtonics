# AI Coastal Threat Alert System

A comprehensive full-stack application for monitoring coastal threats using AI/ML, real-time data ingestion, and automated alert systems.

## 🚀 Features

- **Real-time Data Ingestion**: API endpoints and CSV/Excel file uploads
- **Interactive Dashboard**: Maps, charts, and tables with live updates
- **AI/ML Predictions**: Dynamic risk assessment and anomaly detection
- **Alert System**: SMS/Email notifications with bulk support
- **PWA Ready**: Progressive web app with offline support
- **Responsive Design**: Works across desktop and mobile devices

## 🏗️ Architecture

- **Backend**: FastAPI with WebSocket support and background tasks
- **Frontend**: React + Tailwind CSS + shadcn/ui components
- **Database**: PostgreSQL with SQLAlchemy ORM
- **AI/ML**: Scikit-learn for dynamic model training
- **Real-time**: WebSocket connections for live data updates
- **Maps**: Leaflet with OpenStreetMap integration

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.9+
- Node.js 18+

### 1. Clone and Setup
```bash
git clone <repository-url>
cd ai-coastal-threat-alert
```

### 2. Start with Docker
```bash
docker-compose up -d
```

### 3. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 4. Manual Setup (Alternative)
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## 📁 Project Structure

```
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── models/         # Database models
│   │   ├── routes/         # API endpoints
│   │   ├── services/       # Business logic
│   │   ├── ml/            # AI/ML models
│   │   └── utils/         # Utilities
│   ├── requirements.txt
│   └── main.py
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── pages/         # Page components
│   │   ├── hooks/         # Custom hooks
│   │   └── utils/         # Utilities
│   ├── package.json
│   └── tailwind.config.js
├── docker-compose.yml      # Docker setup
├── Dockerfile.backend      # Backend container
├── Dockerfile.frontend     # Frontend container
└── README.md
```

## 🔧 Configuration

### Environment Variables
Create `.env` files in backend and frontend directories:

**Backend (.env)**
```env
DATABASE_URL=postgresql://user:password@localhost:5432/coastal_threats
SECRET_KEY=your-secret-key
API_KEY=your-api-key
```

**Frontend (.env)**
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

## 📊 Data Sources

The system supports two data ingestion modes:

1. **API Endpoints**: Real-time data fetching with WebSocket updates
2. **File Upload**: CSV/Excel files with dynamic schema detection

### Sample Data Format
```csv
timestamp,latitude,longitude,tide_level,wave_height,wind_speed,risk_score
2024-01-01T10:00:00,19.0760,72.8777,2.5,1.2,15.3,0.7
```

## 🧠 AI/ML Features

- **Dynamic Schema Detection**: Automatically adapts to different CSV formats
- **Real-time Learning**: Continuously updates models with new data
- **Risk Assessment**: Provides threat scores and anomaly detection
- **Forecasting**: Predicts potential threats based on historical patterns

## 🔔 Alert System

- **SMS Alerts**: Mock implementation (ready for MSG91/Textlocal integration)
- **Email Alerts**: Mock implementation (ready for SMTP integration)
- **Bulk Notifications**: Import contact lists via Excel/CSV
- **Template Management**: Customizable alert messages

## 🗺️ Map Features

- **Coastal Regions**: Pre-loaded data for Mumbai and Gujarat
- **Real-time Markers**: Live threat indicators
- **Clustering**: Efficient marker management for large datasets
- **Interactive**: Zoom, pan, and click for details

## 📈 Dashboard Components

- **Live Maps**: Real-time threat visualization
- **Interactive Charts**: Zoomable graphs with filtering
- **Data Tables**: Sortable and searchable records
- **Alert History**: Complete notification log
- **System Status**: Real-time health monitoring

## 🚀 Deployment

### Production Deployment
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

### Environment-Specific Configs
- `docker-compose.yml` - Development
- `docker-compose.prod.yml` - Production
- `docker-compose.test.yml` - Testing

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📚 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints
- `POST /upload` - File upload
- `GET /subscribe` - WebSocket subscription
- `POST /alerts` - Send alerts
- `POST /retrain-model` - Retrain ML model
- `GET /data` - Fetch data
- `GET /predictions` - Get AI predictions

## 🔒 Security Features

- API key authentication
- Input validation and sanitization
- SQL injection prevention
- CORS configuration
- Rate limiting

## 📱 PWA Features

- Offline support with service workers
- Installable on mobile devices
- Push notifications (when supported)
- Responsive design for all screen sizes

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

For issues and questions:
- Create an issue in the repository
- Check the documentation
- Review the API docs at `/docs`

## 🔮 Future Enhancements

- Redis for improved performance
- Multiple ML model support
- Advanced analytics dashboard
- Mobile app (React Native)
- Integration with weather APIs
- Advanced notification channels


