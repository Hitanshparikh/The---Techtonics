import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default markers
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface MapViewProps {
  data: any[];
  selectedRegion: string;
}

const MapView: React.FC<MapViewProps> = ({ data, selectedRegion }) => {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    // Initialize map
    const map = L.map(mapRef.current).setView([20.5937, 78.9629], 5); // Center of India
    
    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    mapInstanceRef.current = map;

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!mapInstanceRef.current) return;

    // Clear existing markers
    mapInstanceRef.current.eachLayer((layer) => {
      if (layer instanceof L.Marker) {
        mapInstanceRef.current?.removeLayer(layer);
      }
    });

    // Add coastal region boundaries
    const mumbaiBounds = L.latLngBounds([18.9, 72.7], [19.3, 73.0]);
    const gujaratBounds = L.latLngBounds([20.0, 68.0], [24.0, 73.0]);

    if (selectedRegion === 'all' || selectedRegion === 'Mumbai') {
      L.rectangle(mumbaiBounds, {
        color: '#0ea5e9',
        weight: 2,
        fillOpacity: 0.1
      }).addTo(mapInstanceRef.current).bindPopup('Mumbai Coastal Region');
    }

    if (selectedRegion === 'all' || selectedRegion === 'Gujarat') {
      L.rectangle(gujaratBounds, {
        color: '#f59e0b',
        weight: 2,
        fillOpacity: 0.1
      }).addTo(mapInstanceRef.current).bindPopup('Gujarat Coastal Region');
    }

    // Add data markers - check if data is valid array
    if (Array.isArray(data) && data.length > 0) {
      data.forEach((item) => {
        if (item.latitude && item.longitude) {
          const riskScore = item.risk_score || 0;
          
          // Create custom icon based on risk level
          const iconColor = riskScore > 0.8 ? '#ef4444' : 
                           riskScore > 0.6 ? '#f97316' : 
                           riskScore > 0.4 ? '#f59e0b' : '#10b981';
          
          const customIcon = L.divIcon({
            className: 'custom-marker',
            html: `<div style="
              width: 20px; 
              height: 20px; 
              background-color: ${iconColor}; 
              border: 2px solid white; 
              border-radius: 50%; 
              box-shadow: 0 2px 4px rgba(0,0,0,0.3);
              display: flex;
              align-items: center;
              justify-content: center;
              color: white;
              font-size: 10px;
              font-weight: bold;
            ">${(riskScore * 100).toFixed(0)}</div>`,
            iconSize: [20, 20],
            iconAnchor: [10, 10]
          });

          const marker = L.marker([item.latitude, item.longitude], { icon: customIcon });
          
          if (mapInstanceRef.current) {
            marker.addTo(mapInstanceRef.current);
          }

          // Create popup content
          const popupContent = `
            <div class="p-2">
              <h3 class="font-bold text-lg mb-2">${item.location || 'Unknown Location'}</h3>
              <div class="space-y-1 text-sm">
                <p><strong>Risk Score:</strong> ${(riskScore * 100).toFixed(1)}%</p>
                <p><strong>Timestamp:</strong> ${new Date(item.timestamp).toLocaleString()}</p>
                ${item.tide_level ? `<p><strong>Tide Level:</strong> ${item.tide_level}m</p>` : ''}
                ${item.wave_height ? `<p><strong>Wave Height:</strong> ${item.wave_height}m</p>` : ''}
                ${item.wind_speed ? `<p><strong>Wind Speed:</strong> ${item.wind_speed} km/h</p>` : ''}
                ${item.anomaly_detected ? '<p class="text-red-600 font-bold">⚠️ Anomaly Detected</p>' : ''}
              </div>
            </div>
          `;

          marker.bindPopup(popupContent);
        }
      });

      // Fit bounds if data exists
      const coordinates = data
        .map(item => [item.latitude, item.longitude] as [number, number])
        .filter(coord => coord[0] && coord[1]);
      
      if (coordinates.length > 0) {
        const bounds = L.latLngBounds(coordinates);
        if (bounds.isValid() && mapInstanceRef.current) {
          mapInstanceRef.current.fitBounds(bounds, { padding: [20, 20] });
        }
      }
    }

  }, [data, selectedRegion]);

  return (
    <div className="w-full h-96 rounded-lg overflow-hidden">
      <div ref={mapRef} className="w-full h-full" />
    </div>
  );
};

export default MapView;


