function getLocation() {

    if (navigator.geolocation) {

        navigator.geolocation.getCurrentPosition(
            showPosition,
            showError
        );

    } else {

        alert("Geolocation is not supported by your browser.");

    }
}


function showPosition(position) {

    const latitude = position.coords.latitude;
    const longitude = position.coords.longitude;

    document.getElementById("latitude").value = latitude;
    document.getElementById("longitude").value = longitude;

    alert("Location captured successfully!");
}


function showError(error) {

    if (error.code === 1) {
        alert("Location permission denied. Please allow location access.");
    }
    else if (error.code === 2) {
        alert("Location unavailable.");
    }
    else if (error.code === 3) {
        alert("Location request timed out.");
    }
    else {
        alert("Unable to get your location.");
    }
}