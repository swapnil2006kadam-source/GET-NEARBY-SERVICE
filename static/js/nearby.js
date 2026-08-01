let map;
let userMarker;
let currentLat;
let currentLon;
let placeMarkers = [];

// Get User Location
if (navigator.geolocation) {

    navigator.geolocation.getCurrentPosition(loadMap, showError);

} else {

    alert("Geolocation not supported.");

}

// Load Map
function loadMap(position) {

    currentLat = position.coords.latitude;
    currentLon = position.coords.longitude;

    document.getElementById("lat").innerText = currentLat;
    document.getElementById("lon").innerText = currentLon;

    // Save location to Flask
    fetch("/save-location", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({

            latitude: currentLat,

            longitude: currentLon

        })

    });

    map = L.map("map").setView([currentLat, currentLon], 15);

    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            attribution: "© OpenStreetMap"
        }
    ).addTo(map);

    userMarker = L.marker([currentLat, currentLon])
        .addTo(map)
        .bindPopup("📍 You are here")
        .openPopup();

}

// Find Nearby Places
function findPlaces(category) {

    // Remove previous markers
    placeMarkers.forEach(marker => map.removeLayer(marker));

    placeMarkers = [];

    let icon = "📍";
let categoryName = "";

switch(category){

    case "hospital":
        icon = "🏥";
        categoryName = "Hospital";
        break;

    case "restaurant":
        icon = "🍽️";
        categoryName = "Restaurant";
        break;

    case "mall":
    icon = "🛍️";
    break;

    case "pharmacy":
        icon = "💊";
        categoryName = "Pharmacy";
        break;

    case "fuel":
        icon = "⛽";
        categoryName = "Petrol Pump";
        break;

}

    fetch(`/get-nearby?category=${category}&lat=${currentLat}&lon=${currentLon}`)

    .then(response => response.json())

    .then(data => {

    const results = document.getElementById("results-list");

    results.innerHTML = "";

    data.forEach(place => {

        // ---------- MAP MARKER ----------

        let marker = L.marker([place.lat, place.lon])

            .addTo(map)

            .bindPopup(`
<div style="min-width:200px">

<h3>${place.name}</h3>

<p>${place.address}</p>

<p>📏 ${place.distance} meters away</p>

</div>
`);

        placeMarkers.push(marker);

        // ---------- RESULT CARD ----------

        const card = document.createElement("div");

        card.className = "place-card";

        card.innerHTML = `

<div class="card-top">

    <<div class="place-icon">${icon}</div>

    <div>

        <h3>${place.name}</h3>

        <p class="address">
            📍 ${place.address}
        </p>

        <span class="distance">
            📏 ${place.distance} meters away
        </span>

    </div>

</div>

<div class="card-buttons">

    <button class="view-btn">
        📍 Locate
    </button>

    <button class="nav-btn">
        🧭 Navigate
    </button>

</div>

`;

        // Locate Button

        card.querySelector(".view-btn").onclick = function(){

            map.setView([place.lat, place.lon],17);

            marker.openPopup();

        };

        // Navigate Button

        card.querySelector(".nav-btn").onclick = function(){

            window.open(

                `https://www.google.com/maps/dir/?api=1&destination=${place.lat},${place.lon}`,

                "_blank"

            );

        };

        results.appendChild(card);

    });

});

}

function showError() {

    alert("Location permission denied.");

}