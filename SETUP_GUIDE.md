# 🚀 AI Coastal Threat Alert System - Setup Guide

This guide will help you get the complete system running locally on your machine.

## 📋 Prerequisites

Before starting, ensure you have the following installed:

- **Python 3.9+** - [Download here](https://www.python.org/downloads/)
- **Node.js 18+** - [Download here](https://nodejs.org/)
- **npm** - Usually comes with Node.js
- **Git** - [Download here](https://git-scm.com/)

## 🚀 Quick Start (Recommended)

### Option 1: Automated Startup Scripts

#### On macOS/Linux:
```bash
chmod +x start_local.sh
./start_local.sh
```

#### On Windows:
```cmd
start_local.bat
```

### Option 2: Manual Setup

## 🔧 Manual Setup Instructions

### Step 1: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p data/uploads
mkdir -p data/models

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Step 2: Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm start
```

### Step 3: Database Setup (Optional)

If you want to use a real PostgreSQL database:

```bash
# Install PostgreSQL or use Docker
docker run --name coastal_db \
  -e POSTGRES_DB=coastal_threats \
  -e POSTGRES_USER=coastal_user \
  -e POSTGRES_PASSWORD=coastal_password \
  -p 5432:5432 \
  -d postgres:15-alpine
```

## 🌐 Access Points

Once everything is running:

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Interactive API Docs**: http://localhost:8000/redoc

## 🧪 Testing the System

### 1. **Dashboard View**
- Navigate to http://localhost:3000
- You'll see the main dashboard with:
  - Interactive map showing Mumbai and Gujarat regions
  - Real-time statistics cards
  - Risk trend charts
  - Active alerts panel

### 2. **File Upload Test**
- Go to the Upload page
- Use the sample data file: `backend/sample_data.csv`
- Upload it to see the system process coastal data

### 3. **API Testing**
- Visit http://localhost:8000/docs
- Test endpoints like:
  - `GET /api/v1/data` - Fetch coastal data
  - `GET /api/v1/data/statistics` - Get data statistics
  - `POST /api/v1/ml/train` - Train ML model

### 4. **WebSocket Test**
- The dashboard automatically connects to WebSocket
- Check browser console for connection status
- Real-time updates will appear as notifications

## 📊 Sample Data

The system comes with sample data for immediate testing:

- **Mumbai Coastal Data**: 25 data points with varying risk levels
- **Gujarat Weather Data**: Simulated weather patterns
- **Mock Alerts**: Sample flood warnings and storm alerts

## 🔍 Troubleshooting

### Common Issues:

#### 1. **Port Already in Use**
```bash
# Check what's using the port
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process or use different ports
uvicorn main:app --reload --port 8001
```

#### 2. **Python Dependencies Issues**
```bash
# Upgrade pip
pip install --upgrade pip

# Clear cache and reinstall
pip cache purge
pip install -r requirements.txt --force-reinstall
```

#### 3. **Node.js Dependencies Issues**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

#### 4. **Map Not Loading**
- Check if Leaflet CSS is loading
- Ensure internet connection for OpenStreetMap tiles
- Check browser console for errors

#### 5. **WebSocket Connection Failed**
- Ensure backend is running on port 8000
- Check if firewall is blocking WebSocket connections
- Verify CORS settings in backend

### Performance Tips:

1. **Backend**: Use `--reload` only in development
2. **Frontend**: Use `npm run build` for production
3. **Database**: Use connection pooling for production
4. **Caching**: Implement Redis for better performance

## 🚀 Production Deployment

### Using Docker Compose:
```bash
# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Environment Variables:
Create `.env` files in both `backend/` and `frontend/` directories:

**Backend (.env):**
```env
DATABASE_URL=postgresql://user:password@localhost:5432/coastal_threats
SECRET_KEY=your-production-secret-key
API_KEY=your-production-api-key
ENVIRONMENT=production
```

**Frontend (.env):**
```env
REACT_APP_API_URL=http://your-domain.com:8000
REACT_APP_WS_URL=ws://your-domain.com:8000
```

## 📚 Next Steps

1. **Connect Real Data Sources**: Replace mock data with actual coastal monitoring APIs
2. **Train ML Models**: Use real coastal data to train risk assessment models
3. **Integrate Notifications**: Connect to real SMS/Email services
4. **Add Authentication**: Implement user login and role-based access
5. **Monitoring**: Add logging, metrics, and health checks
6. **Testing**: Implement comprehensive test suites

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the API documentation at `/docs`
3. Check browser console for frontend errors
4. Check backend logs for server errors
5. Ensure all prerequisites are met

## 🎯 System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│  (PostgreSQL)   │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   WebSocket     │    │   ML Service    │
│   Real-time     │    │   (Scikit-learn)│
│   Updates       │    │   Risk Assessment│
└─────────────────┘    └─────────────────┘
```

## 🎉 Success!

Once everything is running, you'll have a fully functional AI Coastal Threat Alert System with:

- ✅ Real-time dashboard
- ✅ Interactive maps
- ✅ Dynamic charts
- ✅ File upload system
- ✅ API integration
- ✅ ML-powered risk assessment
- ✅ WebSocket real-time updates
- ✅ Responsive design
- ✅ Mock notification system

Enjoy exploring the system! 🚀


