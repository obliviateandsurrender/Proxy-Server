import threading
import json
import time
import datetime
import os
import random
import socket
import email.utils as eut
import base64
import sys
import thread
import copy

proxy_port = 20000

mx = 3
cdir = "./cache"
bsize = 4096
mxc = 8


# checks whether file is already cached or not
def cache_info(lst):

	if lst[0][0] == '/':
		lst[0] = lst[0][1:]
	tp = cdir + "/" + lst[0].replace("/", "__")
	if os.path.isfile(tp):
		tp3 = time.ctime(os.path.getmtime(tp))
		format = "%a %b %d %H:%M:%S %Y"
		tp2 = time.strptime(tp3, format)
	b, a = (tp, None) if not os.path.isfile(tp) else (tp, tp2)
	return a, b

# adding fileurl entry to log
def log_add(lst):

	if lst[0].replace("/", "__") in logs:
		pass
	else:
		logs[lst[0].replace("/", "__")] = []

	logs[lst[0].replace("/", "__")].append(
		{
			"client" : json.dumps(lst[1]),
			"datetime" : time.strptime(time.ctime(), "%a %b %d %H:%M:%S %Y"),
		})


# Retrieves all cache info
def cache_details(lst):

	log_add([lst[1]["total_url"], lst[0]])
	get_access([lst[1]["total_url"]])
	lst[1]["last_mtime"], lst[1]["cache_path"] = cache_info([lst[1]["total_url"]])
	leave_access([lst[1]["total_url"]])

	return lst[1]

# locks fileurl
def get_access(lst):

	lock = threading.Lock() if lst[0] not in locks else locks[lst[0]]
	locks[lst[0]] = lock
	lock.acquire()

# unlocks fileurl
def leave_access(lst):

	tp = 0 if lst[0] not in locks else locks[lst[0]]

	if not tp:
		print "Lock problem"
		sys.exit()
	else:
		tp.release()



# if cache is full then delete the last file
def make_space(fileurl):

	cache_files = os.listdir(cdir)
	if len(cache_files) >= mx:
		get_access([cache_files[-1]])
		os.remove(cdir + "/" + cache_files[-1])
		leave_access([cache_files[-1]])
	return


# Inserts header
def modified_insert(lst):

	lines = lst[0]["client_data"].splitlines()
	while lines[len(lines)-1] == '':
		lines.remove('')

	lines.append("If-Modified-Since: " + time.strftime("%a %b %d %H:%M:%S %Y", lst[0]["last_mtime"]))

	lst[0]["client_data"] = "\r\n".join(lines) + "\r\n\r\n"
	return lst[0]

def parse(client_addr, client_data):

	tp = client_data.splitlines()
	x = tp[len(tp)-1]
	
	while x == '':
		tp.remove('')
		x = tp[len(tp)-1]
	
	tp2 = tp[0].split()

	fir = tp2[0]
	sec = tp2[1]
	url_pos = sec.find("://")

	# get IP's starting index
	if url_pos == -1:
		url = sec
	else:
		url = sec[(url_pos+3):]
	protocol = "http"

	# get port if any and url path
	path_pos = url.find("/")
	if path_pos == -1:
		path_pos = len(url)

	port_pos = url.find(":")


	# change request path accordingly

	server_url = url[:path_pos] if port_pos == -1 or path_pos<port_pos else url[:port_pos]
	server_port = 80 if port_pos == -1 or path_pos<port_pos else int(url[(port_pos+1):path_pos])

	auth_b64 = None

	# build request for server
	sec = url[path_pos:]
	tp2[1] = sec
	tp[0] = ' '.join(tp2)
	client_data = "\r\n".join(tp) + '\r\n\r\n'
	fir = tp2[0]

	return {
		"auth_b64" : auth_b64,
		"method" : fir,
		"protocol" : protocol,
		"client_data" : client_data,
		"total_url" : url,
		"server_url" : server_url,
		"server_port" : server_port,
	}

# Function to handle a request
def handle_request_(client_socket, client_addr, client_data):

	details = parse(client_addr, client_data)

	if details:
		details = cache_details([client_addr, details])
		if details["last_mtime"]:
			details = modified_insert([details])
		serve_get_request([client_socket, client_addr, details])
		client_socket.close()
		print client_addr, "closed"

	else:
		client_socket.close()
		print "No details found"
		return

# Get request handled
def serve_get_request(lst):
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.connect((lst[2]["server_url"], lst[2]["server_port"]))
	server_socket.send(lst[2]["client_data"])

	reply = server_socket.recv(bsize)
	tp = lst[2]["total_url"]
	if not(lst[2]["last_mtime"] and "304 Not Modified" in reply):
		print "Serving %s to %s" % (lst[2]["cache_path"], str(lst[1]))
		make_space(tp)
		get_access(tp)
		fd = open(lst[2]["cache_path"], "w+")
		tp2 = len(reply)
		while tp2:
			
			lst[0].send(reply)
			fd.write(reply)
			reply = server_socket.recv(bsize)
			tp2 = len(reply)

		fd.close()
		leave_access(tp)
		lst[0].send("\r\n\r\n")

	else:
		print "Cached file %s is being returned to %s" % (lst[2]["cache_path"], str(lst[1]))
		get_access(tp)
		f = open(lst[2]["cache_path"], 'rb')
		chunk = f.read(bsize)
		while chunk:
			lst[0].send(chunk)
			chunk = f.read(bsize)
		f.close()
		leave_access(tp)

	server_socket.close()
	lst[0].close()
	return


# Funciton to initialize socket and starts listening.
def start_server():

	try:
		proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		proxy_socket.bind(('', proxy_port))
		proxy_socket.listen(mxc)

		tp3 = str(proxy_socket.getsockname()[0])
		tp4 = str(proxy_socket.getsockname()[1])

		print "Serving proxy on %s port %s ..." % (tp3, tp4)

	except Exception as e:
		print "Error while starting the proxy server.."
		print e
		proxy_socket.close()
		raise SystemExit

	while True:
		try:
			tp, tp2 = proxy_socket.accept()
			tm = str(datetime.datetime.now())
			data = tp.recv(bsize)

			print "%s - [%s] \"%s\"" % (str(tp2), tm, data.splitlines()[0])
			thread.start_new_thread(handle_request_, (tp, tp2, data))

		except KeyboardInterrupt:
			print "\nClosing the proxy server.."
			tp.close()
			proxy_socket.close()
			break


if not os.path.isdir(cdir):
	os.makedirs(cdir)

logs = {}
locks = {}

for file in os.listdir(cdir):
	os.remove(cdir + "/" + file)

start_server()
