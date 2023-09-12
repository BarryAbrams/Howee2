const socket = io.connect('http://' + document.domain + ':' + location.port);

var isProcessing = false;

function sendInput() {
    const inputBox = $('#inputBox');
    const user_input = inputBox.val();
    
    socket.emit('send-input', { input: user_input });
    inputBox.val('');
}

$('#sleep').click(function(event) {
    socket.emit('set-awake-state', { "state":"sleep" });
});

$('#wake').click(function(event) {
    socket.emit('set-awake-state', { "state":"wake" });
});


$('#inputBox').keydown(function(event) {
    if (event.which === 13 && $(this).val().trim() !== '' && !isProcessing) {
        sendInput();
        event.preventDefault();
    }
});

socket.emit('request-state');

let currentLi = null;

socket.on('response', function(data) {
    if (data.type === 'outgoing' || data.type === 'incoming') {
        if (!currentLi) {
            currentLi = $(`<li class="list-group-item message-type-${data.type}"></li>`).append(`<strong>${data.from}</strong> `);
            $('#responseLog').append(currentLi);
            $('#responseLog').append($(".loading"));
            $(".loading").hide();
        }
        currentLi.append(`${data.message} `);
        $('.responseLog-container').scrollTop($('#responseLog')[0].scrollHeight + 20);
    } else if (data.type === 'stop') {
        currentLi = null;
    }
});

socket.on('connect', function() {
    console.log('Connected to the server.');
});

socket.on('emotions', function(data) {
    console.log(data);
});

socket.on('sensors_update', function(data) {
    // console.log(data);
    $("#light").find(".label").text(data.light)
    $("#light").find(".lux").text(Math.floor(data.lux * 100) / 100)

    $("#movement").find(".label").text(data.motion)

    console.log(data)
    if (data.button1) {
        $("#buttons").find("#sleep").removeClass("btn-info").addClass("btn-primary")
    } else {
        $("#buttons").find("#sleep").removeClass("btn-primary").addClass("btn-info")
    }

    if (data.button2) {
        $("#buttons").find("#turbo").removeClass("btn-info").addClass("btn-primary")
    } else {
        $("#buttons").find("#turbo").removeClass("btn-primary").addClass("btn-info")
    }

    let gforces = data.gforces;
    let xRotation = gforces[0] * 90;  // Scale factor, adjust as needed
    let yRotation = gforces[1] * 90;  
    let zRotation = gforces[2] * 90;

    document.querySelector('.cube').style.transform = 
        `rotateX(${xRotation}deg) rotateY(${yRotation}deg) rotateZ(${zRotation}deg)`;


    if (data.motion) {
        $('.cube').addClass("active")
    } else {
        $('.cube').removeClass("active")

    }
    
    // console.log(data.gforces)
});

socket.on('eyes_change', function(data) {
    $(".eyes .selected").removeClass("selected");
    x = data.xPos
    y = data.yPos
    $(".eyes td[data-pos='"+x+","+y+"']").addClass("selected")
});

var high = 0;


socket.on('mouth_change', function(data) {
    // $(".volume").text(data.level)
    if (data.level > high) {
        high = data.level
    }

    let newRadius = data.level * 150;

    if (newRadius < 1) {
        newRadius = 1;
    }

    if (newRadius > 1) {
        $("#micCircle").attr("r", 1);
    }

    $("#volumeCircle").attr("r", newRadius);
});

socket.on('ear_change', function(data) {
    if (data.level > high) {
        high = data.level
    }

    let newRadius = data.level;

    if (newRadius < 1) {
        newRadius = 1;
    }

    $("#micCircle").attr("r", newRadius);
});

socket.on('system_volume', function(data) {
    $('#volumeSlider').val(data.volume)
    
});

socket.on('state_change', function(data) {
    let emotion = "idle"; // default emotion
    if (data.awake_state == "ASLEEP") {
        isProcessing = false;
        emotion = "asleep";
    } else {
        switch (data.action_state) {
            case "PROCESSING":
                isProcessing = true;
                setTimeout(function() {
                    // $(".loading").show();
                }, 250);
                emotion = "thinking"; // or any emotion you associate with PROCESSING
                break;
            case "TALKING":
                isProcessing = true;
                emotion = "excited"; // or any emotion you associate with TALKING
                break;
            // Add more cases as needed
            default:
                isProcessing = false;
                emotion = "idle"; // or any default emotion for awake state
                break;
        }
    }
    $(".face").attr("data-emotion", emotion);
    
});


$(document).ready(function() {
    // Listen for changes to the volume slider
    $('#volumeSlider').on('change', function() {
        var volume = $(this).val();
        socket.emit('set-volume', { volume: volume });
    });

    $("#eyesX, #eyesY").on('change', function() {
        socket.emit('on_eye_position', { x: $("#eyesX").val(), y:$("#eyesY").val() });
    });

    $('#emotionSelector').on('change', function() {
        // Get the selected option's value
        var selectedEmotion = $(this).val();
    
        // Emit the selected emotion to your Socket.io server
        socket.emit('on_emotion_selected', selectedEmotion);
    });
});