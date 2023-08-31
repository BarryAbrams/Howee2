const socket = io.connect('http://' + document.domain + ':' + location.port);

var isProcessing = false;

function sendInput() {
    const inputBox = $('#inputBox');
    const user_input = inputBox.val();
    
    socket.emit('send-input', { input: user_input });
    inputBox.val('');
}

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
                    $(".loading").show();
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
        console.log(data.level)
        if (data.level > high) {
            high = data.level
        }

        let newRadius = data.level * 100;

        if (newRadius < 1) {
            newRadius = 1;
        }

        $("#micCircle").attr("r", newRadius);
    });

    socket.on('system_volume', function(data) {
        $('#volumeSlider').val(data.volume)
        
    });

    $(document).ready(function() {
        // Listen for changes to the volume slider
        $('#volumeSlider').on('change', function() {
            var volume = $(this).val();
            socket.emit('set-volume', { volume: volume });
        });
        
    
    });
    
});
