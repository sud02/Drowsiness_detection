document.addEventListener('DOMContentLoaded', function () {
    const videoElement = document.getElementById('videoElement');
    const startButton = document.getElementById('startButton');
    const stopButton = document.getElementById('stopButton');
    const statusDisplay = document.getElementById('status');
    const ws = new WebSocket('ws://127.0.0.1:8000/ws');
    const alertDisplay = document.getElementById('alertDisplay'); // Make sure to add this element in your HTML

    ws.onopen = function(event) {
        console.log('Connection to server opened');
    }

    ws.onmessage = function(event) {
        console.log('Message from server:', event.data);
        const data = JSON.parse(event.data);
        statusDisplay.innerHTML = `Status: <span>${data}</span>`;

        if (data.alert) {
            // Show alert symbol with "Wake up" message
            alertDisplay.style.display = 'block';
            alertDisplay.innerHTML = '<div class="alert-symbol">⚠️ Wake up!</div>';
            // You might want to add some CSS styles for .alert-symbol to make it big and attention-grabbing
        } else {
            // Hide alert symbol when there is no alert
            alertDisplay.style.display = 'none';
        }
    }

    startButton.onclick = function() {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                videoElement.srcObject = stream;
                ws.send("start");
                console.log('Sent "start" to server');
            })
            .catch(error => {
                console.error('Error accessing the webcam', error);
            });
    };

    stopButton.onclick = async function() {
        if (videoElement.srcObject) {
            videoElement.srcObject.getTracks().forEach(track => track.stop());
            videoElement.srcObject = null;
        }
        ws.send("stop");
        console.log('Sent "stop" to server');
    };

    ws.onclose = function(event) {
        console.log('WebSocket is closed now.');
    };

    ws.onerror = function(err) {
        console.error('WebSocket encountered error: ', err.message, 'Closing socket');
        ws.close();
    };
});
