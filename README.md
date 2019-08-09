## Description

### **Functionality of Proxy Server.**

* A web proxy is a program that acts as an intermediary between a web client (browser or curl) and a web server.
* The request message sent by the client and the response message delivered by the web server pass through the proxy server.
* When using a proxy server , the user is connected to the server, not the Web site in their browser, because the proxy acts as a client on behalf of the user.

### Steps:

* Creating an incoming socket:
  * This creates a socket for the incoming connections. We then bind the socket and then wait for the clients to connect.
* Accept client and process:
  * We wait for the client’s connection request and once a successful connection is made, we dispatch the request in a separate thread, making ourselves available for the next request. This allows us to handle multiple requests simultaneously which boosts the performance of the server multifold times.
* Redirecting the traffic:
  * The main feature of a proxy server is to act as an intermediate between source and destination. Here, we would be fetching data from source and then pass it to the client.

### **Caching**

* Proxy server checks if the requested object is cached or not. Here we have kept 3 responses in cache.
* When the proxy server gets a request, it checks if the requested object is **cached** (i.e. server already has the request webpage or file), and if yes, it returns the object from the cache, without contacting the server.
* If the object is not cached, the proxy retrieves the object from the server, returns it to you and caches a copy of this webpage for future requests if the **Cache-Control** header is set to **must-revalidate**. If the **Cache-Control** header is set to **no-cache**, then the proxy server does not caches the webpage. 
* In case of any further requests if the webpage file is already cached then, the proxy utilize the **If Modified Since** header to check if any  updates have been made, and if not, then serve the response from the cache, otherwise webpage or file is again retrieves from the server.


## Features

1. Threading in proxy server to handle multiple clients.
2. Mutex locks to restrict multiple clients accessing the same file.
3. File is added to the cache when file is at least requested for the 2nd time because adding it the first time will overload the server and there is no guarantee that the object will be requested again.
4. Modular code along with error handling.
5. For caching a folder is created with the name cache and the file is saved using md5 sum as the name.

## Running the code: 

### Server:

Hosted at localhost/19999 or 127.0.0.1/19999

To run:  ```python2 server.py```

### Proxy Server

Hosted at localhost/20000 or 127.0.0.1/20000
To run: ```python2 proxy_server.py```

### Client

The following 2 ways could be used to retrieve the files from the client side.

#### **Using curl commands**

Syntax is :
`curl -x http://host_addr:host_port http://server_addr:server_port/object_location`

In our case it will be:
`curl -x 127.0.0.1:20000  http://127.0.0.1:19999/1.txt`.

#### **Using Browser** 

For browser to use the proxy, you'll need to set the proxy by changing in your system's network settings in case of Chrome and browser's network settings in case of Firefox. You need to give the host and the port number where your proxy server is running.
