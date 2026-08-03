let map;
let markers = {};

function loadUsers() {

    fetch("/live-locations")

    .then(res => res.json())

    .then(users => {

        if (users.length === 0) return;

        if (!map) {

            map = L.map("map").setView(
                [users[0].lat, users[0].lon],
                15
            );

            L.tileLayer(
                "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                {
                    attribution: "© OpenStreetMap"
                }
            ).addTo(map);

        }

        const container = document.getElementById("users-container");

        container.innerHTML = "";

        users.forEach(user => {

            // ---------- MAP ----------

            if (markers[user.id]) {

                markers[user.id]
                    .setLatLng([user.lat, user.lon])
                    .setPopupContent(`
                        <b>${user.name}</b><br>
                        ${user.email}
                    `);

            } else {

                markers[user.id] = L.marker(
                    [user.lat, user.lon]
                )
                .addTo(map)
                .bindPopup(`
                    <b>${user.name}</b><br>
                    ${user.email}
                `);

            }

            // ---------- USER CARD ----------

            container.innerHTML += `

            <div class="user-card">

                <h3>👤 ${user.name}</h3>

                <p>📧 ${user.email}</p>

                <p>
                    ${
                        user.status == "Online"
                        ? "🟢 Online"
                        : "🔴 Offline"
                    }
                </p>

                <p>
                    🕒 Updated ${user.seconds} sec ago
                </p>

                <p>
                    📍 ${user.lat},
                    ${user.lon}
                </p>

                <div class="card-buttons">

<a
href="https://www.google.com/maps?q=${user.lat},${user.lon}"
target="_blank"
class="btn">

🗺 Google Maps

</a>

<button
class="delete-btn"
onclick="deleteLocation(${user.id})">

🗑 Delete

</button>

</div>
            </div>

            `;

        });

    });

}

function deleteLocation(userId){

    if(!confirm("Delete this user's location?")){
        return;
    }

    fetch(`/delete-location/${userId}`,{

        method:"POST"

    })

    .then(res=>res.json())

    .then(data=>{

        if(data.status=="success"){

            loadUsers();

        }

    });

}

loadUsers();

setInterval(loadUsers, 5000);