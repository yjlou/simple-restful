#!/usr/bin/python
"""
  Test under 'test_root'. Some test cases could create 'tests/XXXX' directory.
"""

import fs
import httpd
import json
import os
import params
import random
import SimpleHTTPServer, BaseHTTPServer, httplib
import string
import subprocess
import tempfile
import time
import threading
import unittest
import urllib

DEBUG = 4

"""
Easy hack to temporarily overwrite the root path for testing.
"""
params.HTTP_ROOT = "test_root"


class StoppableHandler(httpd.HttpHandler):

  def do_QUIT(self):
    """
    Kudos http://code.activestate.com/recipes/336012-stoppable-http-server/
    """
    self.server.stop = True

    self.send_response(200)
    self.end_headers()
    self.wfile.write("Get QUIT from client!")

  def log_message(self, format, *args):
    """
    Kudos http://stackoverflow.com/questions/10651052/how-to-quiet-simplehttpserver
    """
    if (DEBUG >= 5):
      super(StoppableHandler, self).log_message(format, *args)
    pass

class StoppableHttpHandler(StoppableHandler):
  pass

class StoppableHttpsHandler(httpd.SecureHTTPRequestHandler, StoppableHandler):
  pass


class StoppableServer():
  """
  Kudos http://code.activestate.com/recipes/336012-stoppable-http-server/
  """
  def serve_forever(self):
    self.stop = False
    self.started = True
    while not self.stop:
      self.handle_request()
    self.socket.close()

class StoppableHttpServer(StoppableServer, httpd.ThreadingHTTP):
  pass

class StoppableHttpsServer(StoppableServer, httpd.ThreadingHTTPS):
  pass


class Catcher():
  """
  Used by the verifier of curl() to catch interested data.

  To dump all headers:

    for h in catcher.headers.keys():
      print "%s: %s" % (h, catcher.headers[h])
  """

  def parse_header(self, out):
    """
    Given the curl output, parse to self.headers dictionary.
    """
    self.headers = {}
    for h in out.split("\r\n\r\n", 1)[0].split("\r\n"):
      x = h.split(":")
      self.headers[x[0]] = ":".join(x[1:]).lstrip()
    return True


class BaseCases():
  """
  Each test creates a standalone HTTP server and creates a standalone directory.
  The /tests/XXXXXXXX/ directory is deleted after the test.

  For class inheriting this, please implement:
    1. curl_protocol for curl. "http" or "https".
    2. curl_args = [].
    3. start_daemon().
  """

  def start_daemon(self):
    assert False == "Please implement this function."

  def setUp(self):

    random.seed()
    self.server_port = random.randint(1024, 65535)
    self.server_url = "%s://localhost:%s" % (self.curl_protocol,
                                             str(self.server_port))
    chars = string.ascii_uppercase + string.digits
    self.server_path = ''.join(random.choice(chars) for _ in range(8))
    self.server_root = "%s/tests/%s/" % (self.server_url, self.server_path)

    # Must init before new thread starts
    self.server = None

    # start thread
    t = threading.Thread(target = self.start_daemon, args=())
    t.daemon = True  # Program exits and leaves threads.
    t.start()

    # wait for server start to accept connection
    while self.server == None:
      pass
    while not hasattr(self.server, 'started'):
      pass
    while self.server.started == False:
      pass

    self.curl("PUT", self.server_root, expect_status = 201)

  """
  
  Arguments:
    expect_output: a string. Assert it matches the output content (exclude headers)
    verifier:  a callback function. Assert verifier(out) returns True.
  """
  def curl(self, method, url, params = {}, accept = "application/json",
           userpass = None,
           expect_status = 200, expect_output = None, verifier = None,
           extra_headers = {}):
    # TODO: use curl.py
    # curl -i -H "Accept: application/json" -X PUT -d "phone=1-800-999-9999"
    #      http://localhost:8888/test
    DEVNULL = open(os.devnull, 'w')
    p = ["%s=%s" % (urllib.quote(k), urllib.quote(v))
                    for (k, v) in params.iteritems()]
    p = "&".join(p)
    a = "Accept: %s" % accept  # TODO: unused?
    up = ["--digest", "--user", userpass] if userpass else []
    headers = []
    for (h, v) in extra_headers:
      headers.append("-H")
      headers.append("%s: %s" % (h, v))
    cmd = ['curl', '-i', '-X', method, "-d", p, url] + up +  \
          self.curl_args + headers
    if DEBUG >= 5: print(cmd)
    pipe = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = DEVNULL)
    (out, _) = pipe.communicate()
    if DEBUG >= 5: print "OUT: " + out

    # parse headers
    out_lines = out.split("\r\n")
    if DEBUG >= 5: print "out_lines: ", out_lines
    status = int(out_lines[0].split(" ")[1])  # HTTP/1.0 200 OK
    # If 401, curl will send another request
    if status == 401:
      i = 1
      while i < len(out_lines) - 1:
        if len(out_lines[i]) == 0:
          next_line = out_lines[i + 1]
          if DEBUG >= 5: print "Second header: [%s]" % next_line
          if next_line[:5] == "HTTP/":
            status = int(next_line.split(" ")[1])  # HTTP/1.0 200 OK
        i = i + 1

    self.assertEqual(status, expect_status)

    if expect_output:
      output = out.split("\r\n\r\n", 1)[1]
      self.assertEqual(output, expect_output)

    if verifier:
      self.assertTrue(verifier(out))

  def test_get_not_exist(self):
    not_exist = "%s%s" % (self.server_root, "no_exist")
    self.curl("GET", not_exist, expect_status = 404)

  def test_put_new_file(self):
    new_file = "%s%s" % (self.server_root, "new_file")
    content = "Line 1 \n Line 2"
    content2 = "Line 1 \n Line 2\nLine 3\n"

    # Upload a new file
    # Expect: 200 OK
    self.curl("PUT", new_file, {"content": content}, expect_status = 201)
    self.curl("GET", new_file, expect_output = content)

    # Upload again
    # Expect: 201 Created
    self.curl("GET", new_file, {"action": "PUT", "content": content},
              expect_status = 201)
    self.curl("GET", new_file, expect_output = content)

    # Try to change the content
    # Expect: 201 created
    self.curl("PUT", new_file, {"content": content2}, expect_status = 201)
    self.curl("GET", new_file, expect_output = content2)

    # clean up
    self.curl("DELETE", new_file)

  def test_create_file_but_a_directory_exists(self):
    new_dir = "%s%s/" % (self.server_root, "new_file")
    self.curl("PUT", new_dir, expect_status = 201)

    new_file = "%s%s" % (self.server_root, "new_file")
    self.curl("PUT", new_file, expect_status = 403)

    # clean up
    self.curl("DELETE", new_dir)

  def test_create_directory_but_a_file_exists(self):
    new_file = "%s%s" % (self.server_root, "new_file")
    self.curl("PUT", new_file, expect_status = 201)

    new_dir = "%s%s/" % (self.server_root, "new_file")
    self.curl("PUT", new_dir, expect_status = 403)

    # clean up
    self.curl("DELETE", new_file)

  def test_delete_nonexist(self):
    filename = "%s%s" % (self.server_root, "new_file")
    self.curl("DELETE", filename, expect_status = 404)

  def test_update_nonexist(self):
    new_file = "%s%s" % (self.server_root, "new_file")
    content = "Line 1 \n Line 2"

    self.curl("UPDATE", new_file, {"content": content}, expect_status = 403)

  def test_update_directory(self):
    new_dir = "%s%s/" % (self.server_root, "new_file")
    new_file = "%s%s" % (self.server_root, "new_file")
    content = "Line 1 \n Line 2"

    self.curl("PUT", new_dir, expect_status = 201)
    self.curl("UPDATE", new_file, {"content": content}, expect_status = 403)

    # clean up
    self.curl("DELETE", new_dir)

  def test_update_file(self):
    new_file = "%s%s" % (self.server_root, "new_file")
    content = "Line 1 \n Line 2"
    content2 = "Line 1 \n Line 2\nLine 3\n"

    # Upload a new file
    # Expect: 200 OK
    self.curl("PUT", new_file, {"content": content}, expect_status = 201)
    self.curl("GET", new_file, expect_output = content)

    # Upload again
    # Expect: 200 OK
    self.curl("UPDATE", new_file, {"content": content2})
    self.curl("GET", new_file, expect_output = content2)

    # Upload again (with action=UPDATE)
    # Expect: 200 OK
    self.curl("GET", new_file, {"action": "UPDATE", "content": content})
    self.curl("GET", new_file, expect_output = content)

    # clean up
    self.curl("DELETE", new_file)

  def test_content_special(self):
    new_file = "%s%s" % (self.server_root, "new_file")
    content = "Line\0 1 \n Line 2\r\n% < & >"

    # Upload a new file
    # Expect: 200 OK
    self.curl("PUT", new_file, {"content": content}, expect_status = 201)
    self.curl("GET", new_file, expect_output = content)

    # clean up
    self.curl("DELETE", new_file)

  def test_ls_dir_in_json(self):
    new_file = "%s%s" % (self.server_root, "new_file")

    # Upload a new file
    # Expect: 200 OK
    self.curl("PUT", new_file, expect_status = 201)
    self.curl("GET", new_file)

    # List the dir
    content = '[{"type": 2, "name": "new_file"}]'
    path = "%s?output_format=json" % self.server_root
    self.curl("GET", path, expect_output = content)

    # List the dir
    content = '[{"type": 2, "name": "new_file"}]'
    self.curl("GET", self.server_root, {'output_format': 'application/json'},
              expect_output = content)

    # clean up
    self.curl("DELETE", new_file)

  def test_get_file_in_json(self):
    new_file = "%s%s" % (self.server_root, "new_file")
    content = "content=xxx"  # recursive description

    # Upload a new file
    # Expect: 200 OK
    self.curl("PUT", new_file, {"content": content}, expect_status = 201)

    #
    # See if "content=xxx" is encoded in the JSON["content"].
    def content_verifier(out):
      output = out.split("\r\n\r\n", 1)[1]
      return json.loads(output)["content"] == content
    self.curl("GET", new_file, {"output": "json"}, verifier = content_verifier)

    #
    # See if Last-Modified in the returned HTTP response headers
    def LM_verifier(out):
      headers = out.split("\r\n\r\n", 1)[0].split("\r\n")
      for h in headers:
        if h.split(":")[0] == "Last-Modified":
          return True
      return False
    self.curl("GET", new_file, {"output": "json"}, verifier = LM_verifier)

    # clean up
    self.curl("DELETE", new_file)

  def test_last_modified(self):
    new_file = "%s%s" % (self.server_root, "new_file")
    content = "v0"

    # Upload a new file
    # Expect: 200 OK
    self.curl("PUT", new_file, {"content": content}, expect_status = 201)

    self.curl("GET", new_file, {}, expect_output = content)

    #
    # See if Last-Modified in the returned HTTP response headers
    def LM_verifier(out):
      headers = out.split("\r\n\r\n", 1)[0].split("\r\n")
      for h in headers:
        if h.split(":")[0] == "Last-Modified":
          return True
      return False
    self.curl("GET", new_file, {}, verifier = LM_verifier)

    #
    # Specify an older if-modified-since, expect full content.
    self.curl("GET", new_file, {}, expect_output = content, extra_headers = [
          ("If-Modified-Since", "Thu, 1 Jan 1970 00:00:00 GMT"),
        ])

    #
    # Specify an newer if-modified-since, expect 304
    self.curl("GET", new_file, {}, expect_output = "", expect_status = 304,
        extra_headers = [
          ("If-Modified-Since", "Thu, 1 Jan 2038 00:00:00 GMT"),
        ])

    # clean up
    self.curl("DELETE", new_file)

  def test_longpoll_no_modify(self):
    new_file = "%s%s" % (self.server_root, "new_file")
    content = "v0"

    # Upload a new file
    # Expect: 200 OK
    self.curl("PUT", new_file, {"content": content}, expect_status = 201)
    catcher = Catcher()
    self.curl("GET", new_file, {}, expect_output = content,
              verifier = lambda out: catcher.parse_header(out))
    last_modified = catcher.headers["Last-Modified"]

    self.curl("GET", new_file, {"longpoll": "3"},
        expect_output = "", expect_status = 304,
        extra_headers = [
          ("If-Modified-Since", last_modified),
        ])

    # clean up
    self.curl("DELETE", new_file)

  def test_longpoll_non_exist(self):
    new_file = "%s%s" % (self.server_root, "new_file")
    content = "v1"

    def delayed_curl():
      time.sleep(3)
      self.curl("PUT", new_file, {"content": content}, expect_status = 201)

    t = threading.Thread(target = delayed_curl, args=())
    t.daemon = True  # Program exits and leaves threads.
    t.start()

    self.curl("GET", new_file, {"longpoll": "6"},
        expect_output = content, expect_status = 200)

    # clean up
    self.curl("DELETE", new_file)

  def test_longpoll_modify(self):
    new_file = "%s%s" % (self.server_root, "new_file")
    content = "v1"
    content2 = "v2"

    # Upload a new file
    # Expect: 200 OK
    self.curl("PUT", new_file, {"content": content}, expect_status = 201)
    catcher = Catcher()
    self.curl("GET", new_file, {}, expect_output = content,
              verifier = lambda out: catcher.parse_header(out))
    last_modified = catcher.headers["Last-Modified"]

    def delayed_curl():
      time.sleep(3)
      self.curl("PUT", new_file, {"content": content2}, expect_status = 201)

    t = threading.Thread(target = delayed_curl, args=())
    t.daemon = True  # Program exits and leaves threads.
    t.start()

    self.curl("GET", new_file, {"longpoll": "6"},
        expect_output = content2, expect_status = 200,
        extra_headers = [
          ("If-Modified-Since", last_modified),
        ], verifier = lambda out: catcher.parse_header(out))
    last_modified2 = catcher.headers["Last-Modified"]

    self.assertNotEqual(last_modified, last_modified2)

    # clean up
    self.curl("DELETE", new_file)

  def test_longpoll_modify_no_if_modified_since_as_chrome(self):
    new_file = "%s%s" % (self.server_root, "new_file")
    content = "v1"
    content2 = "v2"

    # Upload a new file
    # Expect: 200 OK
    self.curl("PUT", new_file, {"content": content}, expect_status = 201)

    def delayed_curl():
      time.sleep(3)
      self.curl("PUT", new_file, {"content": content2}, expect_status = 201)

    t = threading.Thread(target = delayed_curl, args=())
    t.daemon = True  # Program exits and leaves threads.
    t.start()

    self.curl("GET", new_file, {"longpoll": "6"},
        expect_output = content2, expect_status = 200,
        extra_headers = [])

    # clean up
    self.curl("DELETE", new_file)

  def test_http_auth(self):
    self.curl("GET", self.server_url + "/uid/5566", expect_output = "I am 5566\n")
    self.curl("GET", self.server_url + "/noauth")
    self.curl("GET", self.server_url + "/noauth/file")
    self.curl("GET", self.server_url + "/noauth/noauth")
    self.curl("GET", self.server_url + "/noauth/noauth/file")
    self.curl("GET", self.server_url + "/auth", expect_status = 401)
    self.curl("GET", self.server_url + "/auth", userpass = "/auth/.:auth1234")
    self.curl("GET", self.server_url + "/auth/aFirst", expect_status = 401)
    self.curl("GET", self.server_url + "/auth/aFirst", userpass = "/auth/aFirst:a234")
    self.curl("GET", self.server_url + "/auth/auth", expect_status = 401)
    self.curl("GET", self.server_url + "/auth/auth/file", expect_status = 401)
    self.curl("GET", self.server_url + "/auth/noauth", expect_status = 401)
    self.curl("GET", self.server_url + "/auth/noauth/file", expect_status = 401)
    self.curl("GET", self.server_url + "/auth/auth/noauth", expect_status = 401)
    self.curl("GET", self.server_url + "/auth/auth/noauth/file", expect_status = 401)
    self.curl("GET", self.server_url + "/auth/public")

  def tearDown(self):
    self.curl("DELETE", self.server_root)
    self.curl("QUIT", self.server_url)

class TestHttpd(BaseCases, unittest.TestCase):
  curl_protocol = "http"
  curl_args = []

  def start_daemon(self):
    httpd.run_server(False, self.server_port,
                     StoppableHttpServer, StoppableHttpHandler, self)

class TestHttpsd(BaseCases, unittest.TestCase):
  curl_protocol = "https"
  curl_args = ["--insecure"]

  def start_daemon(self):
    httpd.run_server(True, self.server_port,
                     StoppableHttpsServer, StoppableHttpsHandler, self)

if __name__ == '__main__':
  unittest.main()

