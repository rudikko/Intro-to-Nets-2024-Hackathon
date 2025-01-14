# Network Speed Test Client-Server Application
This is a client-server application designed to perform network speed tests using both UDP and TCP protocols. The application allows the client to request a file transfer from the server, specifying the file size and the number of connections for each protocol. The server then handles the requests and provides performance metrics, such as the time taken for the transfer and the speed in bits per second.

## Installation
1. The project uses Python's standard libraries (socket, time, and struct) and also colorama, so if Python is already installed the only additional installation required is colorama (pip install colorama)

## Usage
1. Run the Server: Launch the server by running :
```bash
python Server.py
```

2. Run the client: Launch the client by running :
```bash
python Client.py
```
and after that entering the requested parameters. ( notice they all have to be bigger than 0 )

3. The server will continuously listen for incoming connections and respond to speed test requests.
