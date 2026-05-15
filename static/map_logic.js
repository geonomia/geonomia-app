(function() {
    // Check every 200ms if the map has finished loading
    const checkMap = setInterval(() => {
        const mapContainer = document.querySelector('.leaflet-container');
        
        if (mapContainer) {
            // Check if there are any marker icons inside
            const markers = mapContainer.querySelectorAll('.leaflet-marker-icon');
            
            if (markers.length > 0) {
                // Markers found! Ensure it's visible
                mapContainer.style.setProperty('display', 'block', 'important');
                clearInterval(checkMap);
            } else {
                // No markers yet. We wait. 
                // If after 2 seconds still no markers, hide it.
            }
        }
    }, 200);

    // Safety timeout: if no markers appear after 2 seconds, hide the box
    setTimeout(() => {
        const mapContainer = document.querySelector('.leaflet-container');
        if (mapContainer) {
            const markers = mapContainer.querySelectorAll('.leaflet-marker-icon');
            if (markers.length === 0) {
                mapContainer.style.setProperty('display', 'none', 'important');
            }
        }
        clearInterval(checkMap);
    }, 2000);
})();