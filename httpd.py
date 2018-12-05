#!/usr/bin/python

import BaseHTTPServer
import SimpleHTTPServer
import calendar
import cgi
import composer
import digestauth
import fs
import json
import params
import rest
import threading
import time
# For HTTPS
import os
import socket
import SocketServer
from SocketServer import BaseServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from OpenSSL import SSL


DEBUG = 4


class HttpHandler(SimpleHTTPServer.SimpleHTTPRequestHandler, object):

  def get_output_format(self, qs):
    ret = "HTML"

    # TODO: deprecate output_format
    if qs and "output_format" in qs:
      of = qs["output_format"][0]
    elif qs and "output" in qs:
      of = qs["output"][0]
    else:
      of = self.headers.getheader("Accept")

    if of == "application/json" or of == "json":
      ret = "JSON"
    else:
      ret = "HTML"

    return ret;

  def output_auth_headers(self, status_code, headers):
    if DEBUG >=5 :
      print('STATUS_CODE={}'.format(status_code))
    self.send_response(status_code)

    for (key, value) in headers:
      if DEBUG >=5 :
        print('HEADER: {}={}'.format(key, value))
      self.send_header(key, value)
    self.end_headers()

  def authorized(self, rest, db, http_method):
    uri = self.path
    auth_header = self.headers.getheader("Authorization")
    auth_header = auth_header if auth_header else ""
    da = digestauth.DigestAuth(params.HTTP_REALM, {})

    # First check if the user is authoroized to access the path.
    da.parseHeader(auth_header)
    if "username" in da.params:
      user = da.params["username"]
    else:
      user = None
    if DEBUG >= 5:
      print "'username' in auth_header: %s" % user

    if not rest.can_access(user, self.path):
      if DEBUG >= 5:
        print "The user '%s' cannot access the path '%s'." % (user, self.path)
      status_code, headers, user_r = da.authenticate(http_method, uri, auth_header)
      self.output_auth_headers(status_code, headers)
      return False

    if user is None:
      return True

    password = db.get_password(self.path + "/*")
    if password == "":
      if DEBUG >= 5: print "No password is required for path %s" % self.path
      return True

    password = db.get_password(user)
    # Then, authenticate this user.
    da.setUsers({user: password})
    status_code, headers, user_r = da.authenticate(http_method, uri, auth_header)
    if status_code == 200:
      if DEBUG >= 5:
        print "User '%s' is authenticated as '%s'" % (user, user_r)
      assert user_r == user
      return True

    # Not authenticated, challenge again
    if DEBUG >= 5:
      print "The user '%s' is not authenticated. status_code=%d." %  \
          (user, status_code)
    self.output_auth_headers(status_code, headers)
    return False


  def handle_request(self, http_method):

    db = fs.FileSystem(params.HTTP_ROOT)
    r = rest.Rest(db)

    if not self.authorized(r, db, http_method):
      if DEBUG >= 5:
        print "self.authorized() == False"
      return

    # Parse query string in the URI.
    a = self.path.split("?", 1)
    path = a[0]
    if len(a) >= 2:
      qs = cgi.parse_qs(a[1])
    else:
      qs = None

    # Parse POST, PUT, UPDATE, DELETE data
    content_type = self.headers.getheader('content-type')
    if content_type:
      if DEBUG >= 5:
        print('content_type={}'.format(content_type))
      ctype, pdict = cgi.parse_header(content_type)
      if ctype == 'multipart/form-data':
        if DEBUG >= 5:
          print('multipart/form-data')
        postvars = cgi.parse_multipart(self.rfile, pdict)
      elif ctype == 'application/x-www-form-urlencoded':
        length = int(self.headers.getheader('content-length'))
        postvars = cgi.parse_qs(self.rfile.read(length), keep_blank_values = 1)
        if DEBUG >= 5:
          print('application/x-www-form-urlencoded.length={}'.format(length))
      else:
        postvars = {}
    else:
      postvars = {}

    if qs is None:
      qs = postvars
    else:
      qs = dict(postvars.items() + qs.items())

    if "longpoll" in qs:
      longpoll = float(qs["longpoll"][0])
    else:
      longpoll = 0

    if_modified_since = self.headers.getheader('If-Modified-Since')
    if if_modified_since:
      if_modified_since = calendar.timegm(
                              time.strptime(if_modified_since,
                                            "%a, %d %b %Y %H:%M:%S GMT"))
    else:
      # if_modified_since is not specified, set to current time if
      # longpoll is specified.
      if longpoll:
        if_modified_since = time.time()

    while True:
      # prepare Last-Modified data if the target exists.
      if db.path_type(path.split("/")) == db.NOT_EXIST:
        last_modified = None
      else:
        last_modified = db.get_last_modified(path.split("/"))

      if longpoll and last_modified is None:
        # If this is longpoll and the file is not existed yet, pass through
        # for next iteration.
        pass
      elif if_modified_since and int(if_modified_since) >= int(last_modified):
        status_code = 304
        response_data = ""
      else:
        #
        # Call REST handler !
        (status_code, response_data) = r.handle(http_method, path, qs)
        break

      if longpoll <= 0:
        break
      time.sleep(1)
      longpoll = longpoll - 1

    output_format = self.get_output_format(qs)
    c = composer.Composer(output_format, db)

    (content_type, output) = c.compose(response_data, path)

    self.send_response(status_code)
    self.send_header("Content-type", content_type)
    if last_modified is not None:
      self.send_header("Last-Modified",
          time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(last_modified)))
    self.end_headers()
    self.wfile.write(output)

  def do_GET(self):
    self.handle_request("GET")

  def do_POST(self):
    self.handle_request("POST")

  def do_PUT(self):
    self.handle_request("PUT")

  def do_UPDATE(self):
    self.handle_request("UPDATE")

  def do_DELETE(self):
    self.handle_request("DELETE")


class SecureHTTPServer(BaseHTTPServer.HTTPServer):
  """
  Kudos http://code.activestate.com/recipes/442473-simple-http-server-supporting-ssl-secure-communica/
  openssl req -new -x509 -keyout server.pem -out server.pem -days 365 -nodes
              -newkey rsa:2048

  BUG:
    curl https://localhost:3443 --insecure: NO error
    firefox 16.0.2:
      File "/usr/local/lib/python2.7/dist-packages/OpenSSL/SSL.py", line 851, in _raise_ssl_error
      raise ZeroReturnError()
    chrome 34.0.1847.131 m:
      File "/usr/local/lib/python2.7/dist-packages/OpenSSL/SSL.py", line 864, in _raise_ssl_error
      raise SysCallError(-1, "Unexpected EOF")
  """
  def __init__(self, server_address, HandlerClass):
    BaseServer.__init__(self, server_address, HandlerClass)
    ctx = SSL.Context(SSL.SSLv23_METHOD)
    #server.pem's location (containing the server private key and
    #the server certificate).
    fpem = 'server.pem'
    ctx.use_privatekey_file(fpem)
    ctx.use_certificate_file(fpem)
    self.socket = SSL.Connection(ctx, socket.socket(self.address_family,
                                                    self.socket_type))
    self.server_bind()
    self.server_activate()

  def shutdown_request(self,request):
    request.shutdown()

class SecureHTTPRequestHandler(HttpHandler):
  def setup(self):
    self.connection = self.request
    self.rfile = socket._fileobject(self.request, "rb", self.rbufsize)
    self.wfile = socket._fileobject(self.request, "wb", self.wbufsize)


class ThreadingHTTP(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
  pass
class ThreadingHTTPS(SocketServer.ThreadingMixIn, SecureHTTPServer):
  pass


def run_server(https, port,
               ServerClass = None, HandlerClass = None, child = None):
  server_address = ('', port)

  if not https:
    protocol = "HTTP"
    if ServerClass is None:
      ServerClass = ThreadingHTTP
    if HandlerClass is None:
      HandlerClass = HttpHandler
  else:
    protocol = "HTTPS"
    if ServerClass is None:
      ServerClass = ThreadingHTTPS
    if HandlerClass is None:
      HandlerClass = SecureHTTPRequestHandler

  httpd = ServerClass(server_address, HandlerClass)
  sa = httpd.socket.getsockname()
  if DEBUG >= 5:
    print "Serving %s on %s port %s ..." % (protocol, sa[0], sa[1])

  # For unittest to update the server is up.
  if child:
    child.server = httpd
    child.server.started = True

  httpd.serve_forever()


def main():
  def run_http():
    run_server(False, params.HTTP_PORT)
  def run_https():
    run_server(True, params.HTTPS_PORT)

  threading.Thread(target = run_http).start()
  threading.Thread(target = run_https).start()

if __name__ == '__main__':
  main()
