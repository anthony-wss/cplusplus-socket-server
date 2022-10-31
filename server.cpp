/*
    reference: man7.org
*/

// system call library
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <arpa/inet.h>

// C++ Library
#include <iostream>
#include <thread>
#include <fstream>

// C++ STL
#include <vector>
#include <string>
#include <sstream>
using namespace std;

class Http {
    public:
        string httpVersion, statusCode, contentLen, contentType, connection, body;
        string responseHtml(string filename) {
            ifstream file(filename.c_str());
            string buffer, html;
            while (!file.eof()) {
                getline(file, buffer);
                html.append(buffer);
            }

            httpVersion = "HTTP/1.1";
            statusCode = "200 OK";
            contentLen = to_string(html.length());
            contentType = "text/html";
            connection = "keep-alive";

            stringstream ss;
            ss << httpVersion << ' ' << statusCode << "\r\n" \
                << "Content-Length: " << contentLen << "\r\n" \
                << "Content-Type: "   << contentType << "\r\n" \
                << "Connection: "     << connection << "\r\n" \
                << "\n" << html; 
            return ss.str();
        }
};

class Client {
    public:
        int fd;
        struct sockaddr addr;
        int addrLen;
        thread* td;
    Client() {
        addrLen = sizeof(addr);
    }
};

class Server {
    public:
        void createSocket() {
            // int socket(int domain, int type, int protocol)
            // type: SOCK_DGRAM for udp socket
            if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) == -1) {
                perror("socket error");
                exit(1);
            }
            int enable = 1;
            if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &enable, sizeof(int)) < 0) {
                perror("setsockopt(SO_REUSEADDR) failed");
                exit(1);
            }
        }

        void bindToPort() {
            // int bind(int sockfd, const struct sockaddr *addr, socklen_t addlen)
            if(bind(server_fd, (struct sockaddr *) &addr, sizeof(addr)) == -1) {
                perror("bind error");
                exit(1);
            }
        }

        void listenForConnection() {
            // int listen(int sockfd, int backlog)
            if (listen(server_fd, 16) == -1) {
                perror("listen error");
                exit(1);
            }
        }

        void acceptConnection() {
            // int accept(int sockfd, struct sockaddr *restrict addr, socklen_t *restric addrlen);
            // return a new file descriptor
            Client newClient;
            if ((newClient.fd = accept(server_fd, &newClient.addr, (socklen_t*) &newClient.addrLen)) == -1) {
                perror("accept error");
                exit(1);
            }
            newClient.td = new thread(&Server::serveClient, this, newClient.fd);
            newClient.td->detach();
            clients.push_back(newClient);
            cout << "New client: " << newClient.fd << endl;
        }

        void handelGet(int fd, string s) {
            string response = http.responseHtml("src/index.html");
            if (write(fd, response.c_str(), response.length()) != response.length()) {
                perror("write error");
                exit(1);
            }
        }

        void handelPost(int fd, string s) {
            
        }

        void serveClient(int fd) {
            // ssize_t read(int fd, void *buf, size_t count);
            cout << "Start serving client " << fd << endl;
            char buffer[1024];
            while(read(fd, buffer, sizeof(buffer)) > 0) {
                string s(buffer);
                cout << s << endl;
                if (s.substr(0, 3) == "GET") {
                    handelGet(fd, s);
                }
                else if (s.substr(0, 4) == "POST") {
                    handelPost(fd, s);
                }
                else {
                    cout << "[Unknown Request] Disconnecting Client " << fd << endl;
                    break;
                }
            }
            cout << "Client " << fd << " closed." << endl;
        }

        // close()
        void disconnectClient(int clientId) {
            if(close(clients[clientId].fd) == -1) {
                perror("close error");
                exit(1);
            }
            clients.erase(clients.begin()+clientId);
        }

        // shutdown()
        void closeConnection() {
            if (shutdown(server_fd, SHUT_RDWR) == -1) {
                perror("shutdown error");
                exit(1);
            }
        }

        Server() {
            addr.sin_family = AF_INET;
            addr.sin_port = htons(19777);  // make sure the byte order is correct
            if (inet_aton("140.112.30.57", &addr.sin_addr) == 0) {  // convert the ip string into binary
                perror("inet_aton error");
                exit(1);
            }
        }

    private:
        int server_fd;
        struct sockaddr_in addr;
        vector<Client> clients;
        Http http;
};

int main() {
    Server server;
    server.createSocket();
    server.bindToPort();

    while (1) {
        server.listenForConnection();
        server.acceptConnection();
    }

    server.disconnectClient(0);
    server.closeConnection();
    return 0;
}