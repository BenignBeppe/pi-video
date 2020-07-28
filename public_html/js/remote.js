$(function() {
    var duration = null;
    var time = 0;
    var playing = false;

    function postRequest(endpoint, data) {
        return sendRequest("POST", endpoint, data);
    }

    function sendRequest(method, endpoint, data) {
        let url = "http://192.168.1.65:5000/video/" + endpoint;
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

    function updateStatus() {
        getRequest("status")
            .done((data) => {
                $(".video-url").val(data.url);
                updateTime(data);
                // let seconds = parseFloat(data.time);
                // setTime(seconds);
                playing = data.playing
            });
    }

    function updateTime(data) {
        console.log("> updateTime():", data);
        let seconds = parseFloat(data.time);
        setTime(seconds);
    }

    function setTime(seconds) {
        let progress = seconds / duration * 100.0;
        $(".time progress").attr("value", progress);
        let timestamp = secondsToTimestamp(seconds);
        $(".time .current-time").text(timestamp);
        // $(".time .progress-bar").text(timestamp);
        time = seconds;
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
        postRequest("play_pause")
            .done((data) => {
                playing = data.playing;
            });
    });
    $(".short-backward").click(() => {
        postRequest("back", {duration: 3.0})
            .done(updateTime);
    });
    $(".long-backward").click(() => {
        postRequest("back", {duration: 10.0})
            .done(updateTime);
    });
    $(".short-forward").click(() => {
        postRequest("forward", {duration: 3.0})
            .done(updateTime);
    });
    $(".long-forward").click(() => {
        postRequest("forward", {duration: 10.0})
            .done(updateTime);
    });
    $(".skip-to").click(() => {
        // let timestamp = $(".skip-to-time").val();
        // let timeArray = timestamp.split(":");
        // let hours = timeArray[0];
        // let minutes = timeArray[1];
        // let seconds = timeArray[2];
        postRequest(
            "time",
            {
                hours: $(".skip-to-hours").val(),
                minutes: $(".skip-to-minutes").val(),
                seconds: $(".skip-to-seconds").val()
            }
        )
            .done(updateTime);
    });
    $(".load-video").click(() => {
        loadVideo();
    });
    function loadVideo() {
        $(".load-video").attr("disabled", true);
        let url = $(".video-url").val();
        statusMessage("info", `Loading video from URL: ${url}`);
        postRequest("load", {url: url})
            .done((data) => {
                setDuration(data.duration);
            })
            .fail(() => {
                statusMessage("danger", "Loading video failed.");
            })
            .always(() => {
                $(".load-video").attr("disabled", false);
            });
    };
    $(".video-url").keypress((event) => {
        if(event.which === 13) {
            loadVideo();
        }
    });
    // $(".time").mousedown((event) => {
    //     draggingTime = true;
    // });
    // $(".time").mousemove((event) => {
    //     if(draggingTime) {
    //     }
    // });
    getRequest("duration")
        .done((data) => {
            setDuration(data.duration);
        });

    function setDuration(newDuration) {
        duration = newDuration;
        $(".duration").text(secondsToTimestamp(duration));
    }

    updateStatus();
    setInterval(
        () => {
            if(playing) {
                setTime(time + 1);
                // updateTime();
            }
        },
        1000
    );
    function statusMessage(type, message) {
        let $alert = $("<div></div>")
            .addClass(`alert alert-${type}`)
            .attr("role", "alert")
            .text(message);
        $(".status").prepend($alert);
    };
});
