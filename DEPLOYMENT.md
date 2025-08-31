# 🚀 Coastal Threat Alert System - Deployment Guide

## 🌐 **DEPLOYED APPLICATION**
**Public URL**: https://2b63c35b65e9.ngrok-free.app

---

## 📋 **Deployment Architecture**

### **Components Running:**
1. **FastAPI Backend** → `localhost:8000`
2. **React Frontend** → Built for production
3. **Proxy Server** → `localhost:5000` (combines frontend + backend)
4. **Ngrok Tunnel** → `https://2b63c35b65e9.ngrok-free.app → localhost:5000`

### **How it Works:**
- **Frontend**: Served as static files from production build
- **API Calls**: Proxied from `/api/*` to backend at `localhost:8000`
- **Single URL**: Everything accessible through one ngrok URL

---

## 🎯 **Available Features**

### **Main Application**: https://2b63c35b65e9.ngrok-free.app
- ✅ **Dashboard**: Risk trends with realistic coastal monitoring data
- ✅ **Alerts**: Emergency alert system with SMS capabilities
- ✅ **Data Visualization**: Charts and analytics
- ✅ **SMS Subscription**: Phone number management
- ✅ **Settings**: System configuration

### **API Endpoints**: https://2b63c35b65e9.ngrok-free.app/api/v1/
- ✅ **Data**: `/api/v1/data` - Coastal monitoring data
- ✅ **Trends**: `/api/v1/data/trends` - Risk trend analytics
- ✅ **Statistics**: `/api/v1/data/statistics` - Data summaries
- ✅ **Alerts**: `/api/v1/alerts/` - Alert management
- ✅ **SMS**: `/api/v1/sms/` - SMS subscription system

---

## 🔧 **Local Development**

### **To run locally:**
```bash
# Backend
cd backend
python main_complete.py  # Port 8000

# Frontend (development)
cd frontend  
npm start  # Port 3001

# Combined (production-like)
cd deploy
npm start  # Port 5000
```

---

## 📊 **Database**
- **Type**: SQLite
- **Location**: `backend/coastal_data.db`
- **Data**: 1,017 realistic coastal monitoring records
- **Coverage**: 14 days of data with storm events

---

## 🌊 **Sample Data Included**
- **Locations**: Miami Beach, Charleston Harbor, San Francisco Bay, etc.
- **Metrics**: Tidal levels, wave heights, weather data, risk scores
- **Events**: Storm sequences, anomaly detection
- **Temporal**: Hourly data with seasonal variations

---

## 🚀 **Deployment Status**
✅ **Backend**: Running and accessible  
✅ **Frontend**: Production build deployed  
✅ **Proxy**: Combining services successfully  
✅ **Ngrok**: Public URL active  
✅ **Database**: Populated with realistic data  
✅ **API**: All endpoints functional  

---

## 🔗 **Quick Links**
- **Live App**: https://2b63c35b65e9.ngrok-free.app
- **Dashboard**: https://2b63c35b65e9.ngrok-free.app/dashboard
- **Alerts**: https://2b63c35b65e9.ngrok-free.app/alerts
- **API Docs**: https://2b63c35b65e9.ngrok-free.app/api/v1/

---

## 📱 **Mobile Friendly**
The application is responsive and works on:
- ✅ Desktop browsers
- ✅ Mobile devices  
- ✅ Tablets

---

**🎉 Your Coastal Threat Alert System is now live and accessible from anywhere!**
