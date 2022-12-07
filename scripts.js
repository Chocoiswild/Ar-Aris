
const myAPIKey = "677a90ba388d487ca1e1d14c2d12a16e";

// The Leaflet map Object
const map = L.map('map', {zoomControl: false}).setView([41.7151, 44.8271], 11);

// Retina displays require different mat tiles quality
const isRetina = L.Browser.retina;

const baseUrl = "https://maps.geoapify.com/v1/tile/osm-bright/{z}/{x}/{y}.png?apiKey={apiKey}";
const retinaUrl = "https://maps.geoapify.com/v1/tile/osm-bright/{z}/{x}/{y}@2x.png?apiKey={apiKey}";

// Add map tiles layer. Set 20 as the maximal zoom and provide map data attribution.
L.tileLayer(isRetina ? retinaUrl : baseUrl, {
attribution: 'Powered by <a href="https://www.geoapify.com/" target="_blank">Geoapify</a> | <a href="https://openmaptiles.org/" rel="nofollow" target="_blank">© OpenMapTiles</a> <a href="https://www.openstreetmap.org/copyright" rel="nofollow" target="_blank">© OpenStreetMap</a> contributors',
apiKey: myAPIKey,
maxZoom: 20,
id: 'osm-bright'
}).addTo(map);

// add a zoom control to bottom-right corner
L.control.zoom({
    position: 'bottomright'
}).addTo(map);

// check the available autocomplete options on the https://www.npmjs.com/package/@geoapify/geocoder-autocomplete 
const autocompleteInput = new autocomplete.GeocoderAutocomplete(
                        document.getElementById("autocomplete"), 
                        myAPIKey, 
                        {});

// Only allow results within a 15k radius of Tbilisi center
autocompleteInput.addFilterByCircle(
    {lon: 44.8271, lat: 41.7151, radiusMeters: 15000}
  );

// generate an marker icon with https://apidocs.geoapify.com/playground/icon
const markerIcon = L.icon({
iconUrl: `https://api.geoapify.com/v1/icon/?type=awesome&color=%232ea2ff&size=large&scaleFactor=2&apiKey=${myAPIKey}`,
iconSize: [38, 56], // size of the icon
iconAnchor: [19, 51], // point of the icon which will correspond to marker's location
popupAnchor: [0, -60] // point from which the popup should open relative to the iconAnchor
});

let marker;



autocompleteInput.on('select', (location) => {
    // Add marker with the selected location
    if (marker) {
        marker.remove();
    }
    
    if (location) {
        marker =  L.marker([location.properties.lat, location.properties.lon], {
            icon: markerIcon
            }).addTo(map);
        document.getElementById("address").value = JSON.stringify(location.properties);
        console.log(JSON.stringify(location.properties));
        map.setZoom(16);
        map.panTo([location.properties.lat, location.properties.lon]);
       
        
    }


    // Do something with the results[]
});  


