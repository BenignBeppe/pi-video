$(function() {
    var duration = null;

    function postRequest(endpoint, data) {
        return sendRequest("POST", endpoint, data);
    }

    function sendRequest(method, endpoint, data) {
        let url = "http://192.168.0.13:5000/video/" + endpoint;
        let request = $.ajax({
            type: method,
            url: url,
            data: data,
            beforeSend: (jqxhr,settings) => {
                console.log("Sending request:", url, data);
            }
        })
            .fail((jqxhr, message, error) => {
                console.log("Request failed:", error, message, url);
            });
        return request;
    }

    function getRequest(endpoint, data) {
        return sendRequest("GET", endpoint, data);
    }

    function updatePosition() {
        getRequest("position")
            .done((data) => {
                let seconds = parseFloat(data.position);
                let progress = seconds / duration * 100.0;
                $(".position .progress-bar").css("width", progress + "%");
                let timestamp = secondsToTimestamp(seconds);
                $(".position .progress-bar").text(timestamp);
            });
    }

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
        let timestamp = hours + ":" + minutes + ":" + seconds;
        return timestamp;
    }

    $(".play").click(() => {
        postRequest("play_pause");
    });
    $(".short-backward").click(() => {
        postRequest("back", {duration: 3.0});
    });
    $(".long-backward").click(() => {
        postRequest("back", {duration: 10.0});
    });
    $(".short-forward").click(() => {
        postRequest("forward", {duration: 3.0});
    });
    $(".long-forward").click(() => {
        postRequest("forward", {duration: 10.0});
    });
    $(".position").mousedown((event) => {
        draggingPosition = true;
    });
    $(".position").mousemove((event) => {
        if(draggingPosition) {
        }
    });
    getRequest("duration")
        .done((data) => {
            setDuration(data.duration);
        });
    function setDuration(newDuration) {
        duration = newDuration;
        $(".duration").text(secondsToTimestamp(duration));
    };
    updatePosition();
    setInterval(() => {
            updatePosition();
        },
        1000
    );
    $(".skip-to").click(() => {
        let timestamp = $(".skip-to-time").val();
        let timeArray = timestamp.split(":");
        let hours = timeArray[0];
        let minutes = timeArray[1];
        let seconds = timeArray[2];
        postRequest(
            "position",
            {
                hours: hours,
                minutes: minutes,
                seconds: seconds
            }
        );
    });
    $(".load-video").click(() => {
        let url = $(".video-url").val();
        statusMessage("info", `Loading video from URL: ${url}`);
        postRequest("load", {url: url})
            .done((data) => {
                setDuration(data.duration);
            })
            .fail((data) => {
                statusMessage("danger", "Loading video failed.");
            });
    });
    function statusMessage(type, message) {
        let $alert = $("<div></div>")
            .addClass(`alert alert-${type}`)
            .attr("role", "alert")
            .text(message);
        $(".status").prepend($alert);
    };
});
