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
