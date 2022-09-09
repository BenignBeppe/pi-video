document.querySelector(".load").onclick = () => {
    let pageUrl = document.querySelector("#page-url").value;
    post("/load", {url: pageUrl});
};

function post(path, parameters) {
    let request = new XMLHttpRequest();
    request.open("POST", path);
    request.setRequestHeader(
        "Content-Type",
        "application/x-www-form-urlencoded"
    );
    if(parameters) {
        var data = new URLSearchParams();
        for(let [key, value] of Object.entries(parameters)) {
            data.append(key, value);
        }
    }
    request.send(data);
}

document.querySelector(".skip-to").onclick = () => {
    let parameters = {
        hours: document.querySelector(".skip-to-hours").value,
        minutes: document.querySelector(".skip-to-minutes").value,
        seconds: document.querySelector(".skip-to-seconds").value
    };
    post("/skip-to", parameters);
};

document.querySelector(".play-pause").onclick = () => {
    post("/play-pause");
};

document.querySelector(".skip-back-long").onclick = () => {
    post("/skip-back-long");
};

document.querySelector(".skip-back-short").onclick = () => {
    post("/skip-back-short");
};

document.querySelector(".skip-forward-short").onclick = () => {
    post("/skip-forward-short");
};

document.querySelector(".skip-forward-long").onclick = () => {
    post("/skip-forward-long");
};

let timeEventSource = new EventSource("/events");
let currentTimeLabel = document.querySelector(".current-time");
let progressBar = document.querySelector(".progress-bar");

timeEventSource.addEventListener("time", (event) => {
    let data = JSON.parse(event.data);
    currentTimeLabel.textContent = secondsToTimestamp(data.time);
    progressBar.classList.remove("loading");
    progressBar.style.width = data.progress * 100 + "%";
    progressBar.textContent = "";
});

timeEventSource.addEventListener("loading", () => {
    progressBar.classList.add("loading");
    progressBar.style.removeProperty("width");
    progressBar.textContent = "Loading...";
});

function secondsToTimestamp(totalSeconds) {
    let time = new Date(0, 0, 0, 0, 0, totalSeconds);
    let hours = time.getHours();
    let minutes = time.getMinutes();
    if(minutes < 10) {
        minutes = "0" + minutes;
    }
    let seconds = time.getSeconds();
    if(seconds < 10) {
        seconds = "0" + seconds;
    }
    let timestamp = `${hours}:${minutes}:${seconds}`;
    return timestamp;
}
