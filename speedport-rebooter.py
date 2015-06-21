## Speedport Hybrid Rebooter by David Ordnung   
## 
## This will restart your Speedport Hybrid.
## With this you can for example restart your Speedport in a specific time interval (Crontab on Linux)
## Your device have to be in the local network and have to be access to the configurator!
##
## INSTALL INSTRUCTION         
##
## Linux (Type commands in terminal):
##     - Install requirements:
##         - Install Python (2.7):  sudo apt-get install build-essential python
##         - Download PyCrypto:     wget https://github.com/dlitz/pycrypto/archive/v2.7a1.zip
##         - Unzip PyCrypto:        unzip v2.7a1.zip && cd pycrypto-2.7a1
##         - Install PyCrypto:      sudo python setup.py install
##     - Set Config below!
##     - This will restart your Speedport Hybrid: python speedport-rebooter.py
##
## Windows:
##     - Install requirements:
##         - Install Python (2.7):  https://www.python.org/downloads/
##         - Download PyCrypto:     https://github.com/dlitz/pycrypto/archive/v2.7a1.zip
##         - Unzip PyCrypto and go into folder
##         - Install PyCrypto:  python setup.py install
##         - You may need a compiler environment like Visual Studio!
##     - Set Config below!
##     - This will restart your Speedport Hybrid: python speedport-rebooter.py

## CONFIG

device_password  =  "password"                # The device password for login
speedport_url    =  "http://speedport.ip/"    # The URL to the Speedport Hybrid Configurator

##
## DO NOT CHANGE ANYTHING BELOW THIS LINE
##

from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Cipher import AES
import time
import sys
import socket
import json
import binascii
import urllib
import urllib2
import cookielib

login_json = "data/Login.json"
reboot_json = "data/Reboot.json"
problem_handling = "html/content/config/problem_handling.html"
challenge_val = ""
derivedk = ""

http_header = {"Content-type": "application/x-www-form-urlencoded", "charset": "UTF-8"}
cookies = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies))
socket.setdefaulttimeout(7)

# URL has to end with slash
if not speedport_url.endswith("/"):
	speedport_url += "/"

# Gets the challenge_val token from login page
def get_challenge_val():
	global challenge_val
	
	json_string = open_site(speedport_url + login_json, {"csrf_token": "nulltoken", "showpw": 0, "challengev": "null"})
	json_object = string_to_json(json_string)
	
	# Check valid response
	for x in json_object:
		if x["vartype"] == "status":
			if x["varid"] == "status":
				if x["varvalue"] != "ok":
					sys.exit("Couldn't retrieve challengev at %s successfully" % (speedport_url + login_json))
		if x["vartype"] == "value":
			if x["varid"] == "challengev":
				challenge_val = x["varvalue"]

# Login with devices password
def login():
	global derivedk
	
	# Hash password with challenge_val
	sha256_full = SHA256.new()
	sha256_full.update("%s:%s" % (challenge_val, device_password))
	encrypted_password = sha256_full.hexdigest()
	
	# Hash only password
	sha256_passwort = SHA256.new()
	sha256_passwort.update(device_password)
	sha256_loginpwd = sha256_passwort.hexdigest()
	
	# Get hashed derivedk
	derivedk = binascii.hexlify(PBKDF2(sha256_loginpwd, challenge_val[:16], 16, 1000))
	
	# Finally login
	json_string = open_site(speedport_url + login_json, {"csrf_token": "nulltoken", "showpw": 0, "password": encrypted_password})
	json_object = string_to_json(json_string)
	
	# Check valid response
	for x in json_object:
		if x["vartype"] == "status":
			if x["varid"] == "login":
				if x["varvalue"] != "success":
					sys.exit("Failed to login at URL %s" % (speedport_url + login_json))
			if x["varid"] == "status":
				if x["varvalue"] != "ok":
					sys.exit("Couldn't login at URL %s successfully" % (speedport_url + login_json))
	
	# Set needed cookies
	set_cookie("challengev", challenge_val)
	set_cookie("derivedk", derivedk)

# Reboots the Speedport
def reboot():
	csrf_token = get_reboot_csrf()
	
	# Check if valid crsf token found
	if csrf_token == "nulltoken":
		sys.exit("You don't seem to be logged in. Please try again")
	
	# Hash reboot command
	aes = AES.new(binascii.unhexlify(derivedk), AES.MODE_CCM, binascii.unhexlify(challenge_val[16:32]), mac_len=8)
	aes.update(binascii.unhexlify(challenge_val[32:48]))
	encrypted = aes.encrypt_and_digest("reboot_device=true&csrf_token=%s" % urllib.quote_plus(csrf_token))
	
	# Get reboot token
	token = binascii.hexlify(encrypted[0] + encrypted[1])
	
	# Reboot Speedport with token
	json_string = open_site(speedport_url + reboot_json, token)
	json_object = string_to_json(json_string)
	
	# Check valid response
	for x in json_object:
		if x["vartype"] == "status":
			if x["varid"] == "status":
				if x["varvalue"] != "ok":
					sys.exit("Couldn't reboot at %s successfully" % (speedport_url + reboot_json))

# Waits until Speedport is available again
def wait_rebooting():
	start = time.time()
	
	while True:
		try:
			open_site(speedport_url + reboot_json, None)
			break
		except:
			# Only try for 4 minutes
			if time.time() - start > 240:
				sys.exit("Speedport still not rebooted after 4 minutes")

# Gets the crsf token from problem handling page
def get_reboot_csrf():
	html = open_site(speedport_url + problem_handling, None)
	start = html.find("csrf_token")
	
	# Found a crsf token?
	if start == -1:
		sys.exit("Couldn't find csrf_token at URL %s" % (speedport_url + problem_handling))
	
	# Get raw token
	end = html.find(";", start)
	return html[(start + len("csrf_token =  \"") - 1) : (end - 1)]

# Opens a specific site
def open_site(url, params):
	# Params only for post requests and dicts
	if params != None and type(params) is dict:
			params = urllib.urlencode(params)
	
	# Open URL
	req = urllib2.Request(url, params, http_header)
	res = opener.open(req)
	
	# Return result
	return res.read()

# Converts a string to a json object
def string_to_json(string):
	# Replace special tokens
	string = string.strip().replace("\n", "").replace("\t", "")
	
	# Some strings are invalid JSON object (Additional comma at the end...)
	if string[-2] == ",":
		string_list = list(string)
		string_list[-2] = ""
		
		return json.loads("".join(string_list))
	
	return json.loads(string)

# Sets new cookies
def set_cookie(name, value):
	cookie = cookielib.Cookie(version=0, name=name, value=value, port=None, port_specified=False, domain=speedport_url.replace("http://", "").replace("/", ""), domain_specified=False, domain_initial_dot=False, path="/", path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={"HttpOnly": None}, rfc2109=False)
	cookies.set_cookie(cookie)

# At first get challenge_val
get_challenge_val()

# Then login
print ("Logging in...")
login()

# Then reboot
print ("Start Rebooting...")
reboot()

# Then wait until rebooted
print ("Wait until rebooting finished...")
wait_rebooting()

# Finished
print ("Rebootet Speedport successfully!")