const myAPIKey = "677a90ba388d487ca1e1d14c2d12a16e";

// The Leaflet map Object
const map = L.map('map', {zoomControl: false}).setView([41.7151, 44.8271], 10.2);

// Retina displays require different mat tiles quality
const isRetina = L.Browser.retina;

const baseUrl = "https://maps.geoapify.com/v1/tile/osm-bright/{z}/{x}/{y}.png?apiKey={apiKey}";
const retinaUrl = "https://maps.geoapify.com/v1/tile/osm-bright/{z}/{x}/{y}@2x.png?apiKey={apiKey}";

// Add map tiles layer. Set 20 as the maximal zoom and provide map data attribution.
L.tileLayer(isRetina ? retinaUrl : baseUrl, {
attribution: 'Powered by <a href="https://www.geoapify.com/" target="_blank">Geoapify</a> | <a href="https://openmaptiles.org/" rel="nofollow" target="_blank">© OpenMapTiles</a> <a href="https://www.openstreetmap.org/copyright" rel="nofollow" target="_blank">© OpenStreetMap</a> contributors',
apiKey: myAPIKey,
maxZoom: 25,
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

// generate n marker icon with https://apidocs.geoapify.com/playground/icon
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
            icon: markerIcon,
            }).addTo(map);
            map.setZoom(15);
            map.panTo([location.properties.lat, location.properties.lon]);
            // Iterate over municipalities to find which one the location is within, 
            municipalities.eachLayer(function(memberLayer) {
                if (memberLayer.contains(marker.getLatLng())) {
                    console.log(memberLayer.feature.properties.NAME_EN);
                    // Assign municipality to form's district field
                    document.getElementById("district").value = memberLayer.feature.properties.NAME_EN
                }
                });
            document.getElementById("address").value = JSON.stringify(location.properties);
            console.log(JSON.stringify(location.properties));
    }

});  


// Add district layers to map\
// Trialling doing it automatically so user's can't make a mistake

// var layer_style = {
//     "fill-opacity": 0.7,
//     // "color": "#d2e6fc",
// }
var municipalities = L.geoJson(json_municipaliteti1, {
    // fillColor: "#d2e6fc",
    // fillOpacity: .5,
    // color: "#00438a",
    // attribution: '<a href=""></a>',
    // onEachFeature: pop_name,
    // style: layer_style
})

// function pop_name( feature, layer) {
//     layer.bindPopup(feature.properties.NAME_EN);
// }


// Script for enabling/disabling the phone number field
// depending on a user's notification preference
let preference = document.querySelector("#preference");
let input_phone = document.querySelector("#phone");

input_phone.disabled = true;

preference.addEventListener("change", stateHandle);

function stateHandle() {
    if (document.querySelector("#preference").value === "both" || "text") {
        input_phone.disabled = false;
    } else {
        input_phone.disabled = true;
    }
    if (document.querySelector("#preference").value === "email") {
        input_phone.value = "";
        input_phone.disabled = true;
    }
}

