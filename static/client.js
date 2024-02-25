// peer connection
var pc = null;
var dc = null, dcInterval = null;
var audio1 = "nn";
var stopper_cnt = 0

start_btn = document.getElementById('start');
stop_btn = document.getElementById('stop');
statusField = document.getElementById('status');

// function generateUUID() { // Public Domain/MIT
//     var d = new Date().getTime();//Timestamp
//     var d2 = ((typeof performance !== 'undefined') && performance.now && (performance.now()*1000)) || 0;//Time in microseconds since page-load or 0 if unsupported
//     return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
//         var r = Math.random() * 16;//random number between 0 and 16
//         if(d > 0){//Use timestamp until depleted
//             r = (d + r)%16 | 0;
//             d = Math.floor(d/16);
//         } else {//Use microseconds since page-load if supported
//             r = (d2 + r)%16 | 0;
//             d2 = Math.floor(d2/16);
//         }
//         return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
//     });
// }

// var sender=generateUUID();
// function send_message(){
//     var output=$("#output").val();
    
//     console.log(output);

//     if(output.length<=0){
//         return;
//     }
//     var xhr = new XMLHttpRequest();
//     x = xhr.open('GET', 'http://192.168.31.130:5025/message?sender='+sender+'&output=' + encodeURIComponent(output), true);
//     //x = xhr.open('GET', 'https://noctest.gplex.net:5566/message?sender='+sender+'&output=' + encodeURIComponent(output), true);
//     console.log('XHR request initialized');
//     var ul = document.getElementById('history');

//     ul.innerHTML += `<span hidden class='g-disha-single-speech'>${output}</span>`;
//     ul.innerHTML += `<span class='g-disha-single-speech'>...</span>`;

//     xhr.onreadystatechange = function() {
//       if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
//         var data = JSON.parse(xhr.responseText);
//         console.log(data[0])
//         let audioData = atob(data[0].audio);
//         let audioArray = new Uint8Array(audioData.length);
//         for (let i = 0; i < audioData.length; i++) {
//           audioArray[i] = audioData.charCodeAt(i);
//         }
//         let audioBlob = new Blob([audioArray.buffer], { type: 'audio/wav' });

//         // Create a URL for the blob
//         var url = URL.createObjectURL(audioBlob);

//         ul.removeChild(ul.lastElementChild);
//         ul.innerHTML += `<span class='g-disha-single-speech'>${data[0].bt}</span>`;
//         // Create a new Audio object and play the audio
//         audio1 = new Audio(url);
//         audio1.autoplay = true;

//         $("#output").val("");
//       }
//     };

//     xhr.onerror = function () {
//     // Handle the error case
//     console.error('An error occurred while making the request.');
//     };

//     xhr.send(null);
// }


function btn_show_stop() {
    start_btn.classList.add('d-none');
    stop_btn.classList.remove('d-none');
}

function btn_show_start() {
    stop_btn.classList.add('d-none');
    start_btn.classList.remove('d-none');
    statusField.innerText = 'Press start';
}

function negotiate() {
    return pc.createOffer().then(function (offer) {
        return pc.setLocalDescription(offer);
    }).then(function () {
        return new Promise(function (resolve) {
            if (pc.iceGatheringState === 'complete') {
                resolve();
            } else {
                function checkState() {
                    if (pc.iceGatheringState === 'complete') {
                        pc.removeEventListener('icegatheringstatechange', checkState);
                        resolve();
                    }
                }

                pc.addEventListener('icegatheringstatechange', checkState);
            }
        });
    }).then(function () {
        var offer = pc.localDescription;
        console.log(offer.sdp);
        return fetch('offer', {
            body: JSON.stringify({
                sdp: offer.sdp,
                type: offer.type,
            }),
            headers: {
                'Content-Type': 'application/json'
            },
            method: 'POST'
        });
    }).then(function (response) {
        return response.json();
    }).then(function (answer) {
        console.log(answer.sdp);
        return pc.setRemoteDescription(answer);
    }).catch(function (e) {
        console.log(e);
        btn_show_start();
    });
}

function performRecvText(str) {
    document.getElementById('output').value = str;

}

function performRecvPartial(str) {
    document.getElementById('output').value = str;

}

function starter(){
    if(stopper_cnt > 0){
        stopper_cnt = 0
    }

    start();

    k = setInterval(function(){
        if(stopper_cnt > 100  ){
            console.log("Stopping...")
            stop();
            clearInterval(k);
        }
    }, 50);

}

function start() {
    if (audio1 !== 'nn') {
        audio1.pause();
        audio1.currentTime = 0;
    }
    btn_show_stop();

    var newText = ""

    statusField.innerText = 'Connecting...';
    var config = {
        sdpSemantics: 'unified-plan'
    };

    pc = new RTCPeerConnection(config);

    dc = pc.createDataChannel('result');
    dc.onclose = function () {
        clearInterval(dcInterval);
        console.log('Closed data channel');
        btn_show_start();
    };
    dc.onopen = function () {
        console.log('Opened data channel');
    };
    dc.onmessage = function (messageEvent) {
        statusField.innerText = "Listening... say something";

        if (!messageEvent.data) {
            return;
        }
        newText = newText + messageEvent.data + " "
        document.getElementById('output').value = newText;

        let voskResult;
        try {
            voskResult = JSON.parse(messageEvent.data);
        } catch (error) {
            console.error(`ERROR: ${error.message}`);
            return;
        }
        if ((voskResult.text?.length || 0) > 0) {
            performRecvText(voskResult.text);
        } else if ((voskResult.partial?.length || 0) > 0) {
            stopper_cnt = 0
            performRecvPartial(voskResult.partial);
        }else{
            stopper_cnt += 1
        }
    };

    pc.oniceconnectionstatechange = function () {
        if (pc.iceConnectionState == 'disconnected') {
            console.log('Disconnected');
            btn_show_start();
        }
    }

    var constraints = {
        audio: true,
        video: false,
    };

    navigator.mediaDevices.getUserMedia(constraints).then(function (stream) {
        stream.getTracks().forEach(function (track) {
            pc.addTrack(track, stream);
        });
        return negotiate();
    }, function (err) {
        console.log('Could not acquire media: ' + err);
        btn_show_start();
    });
}

function stop() {
    // close data channel
    if (dc) {
        dc.close();
    }

    // close transceivers
    if (pc.getTransceivers) {
        pc.getTransceivers().forEach(function (transceiver) {
            if (transceiver.stop) {
                transceiver.stop();
            }
        });
    }

    // close local audio / video
    pc.getSenders().forEach(function (sender) {
        sender.track.stop();
    });

    setTimeout(function () {
        pc.close();
    }, 500);
}

