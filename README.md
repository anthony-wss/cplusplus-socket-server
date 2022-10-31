# cplusplus-socket-server

This project is written with full object-oriented C++ languages. A client thread will be created once a new connection is accept, so it allows multiple client communications.

The HTTP protocol, Server, Client, ... are all C++'s class. Here's the structure of `server.cpp`:

```bash
server.cpp/
├─ class Http/
│  ├─ responseHtml()
├─ class Client/
│  ├─ fd
│  ├─ thread
│  ├─ address
├─ class Server/
│  ├─ createSocket()
│  ├─ bindToPort()
│  ├─ listenForConnection()
│  ├─ acceptConnection()
│  ├─ handelGet()
│  ├─ serveClient()
│  ├─ disconnectClient()
│  ├─ closeConnection()
├─ main
```

## Deploy Site
http://140.112.30.57:19777

This server is listening for the connection on the workstation of CSIE. If the server is down please contact: b09902033@csie.ntu.edu.tw to reboot it.

## Compile & Run

```bash
# compile
g++ server.cpp -o server
# run
./server
```