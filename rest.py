#!/usr/bin/python
#
#  Access control, file/directory permission, authorization.
#
#  TODO:
#    ~ for home of HTTP authenticator
#

DEBUG = 4

class Rest():

  def __init__(self, db):
    self.db = db

  def can_access(self, user, path):
    """
    If the user is permitted to access this directory
   
      'user' -- String. The username in the Authenticate header.
                None if no authenticate header.
      'path' -- String. The path to access.
                Can be a file or a directory.
   
    Returns: True if the user is accessible to the path.
    """
    if not self.db.need_authentication(path):
      # Free for all. No need to authenticate.
      if DEBUG >= 5:
        print "The path '%s' is free to access (not under .htpasswd)." % path
      return True

    if user is None:
      if DEBUG >= 5:
        print "The path '%s' isn't free to access, but no user is provided." % path
      return False

    #
    # return error if the 'user' is not prefix of 'path'.
    #
    i = 0
    u = self.db.safe_path(user.split("/")).split("/")
    p = self.db.safe_path(path.split("/")).split("/")
    if DEBUG >= 5:
      print "User: ", u
      print "Path: ", p
    if len(u) > len(p):
      return False
    for i in range(len(u)):
      if u[i] != p[i]:
        return False

    if DEBUG >= 5:
      print "The user '%s' is able to access the path '%s'." % (user, path)
    return True


  def handle(self, http_method, full_path, args = None):
    if args and "action" in args:
      http_method = args["action"][0]

    if args and "content" in args:
      content = args["content"][0]
    else:
      content = ""

    if len(full_path) > 1 and full_path[-1] == "/":
      slash_at_end = True
    else:
      slash_at_end = False

    # split path into array
    path = full_path.split("/")

    type = self.db.path_type(path)

    if http_method == "GET":
      if type is self.db.DIR:
        ret = self.db.get_dir(path)
        status_code = 200
      elif type is self.db.FILE:
        ret = self.db.get_file(path)
        status_code = 200
      else:
        ret = "GET %s is not found." % full_path
        status_code = 404

    elif http_method == "PUT":
      if slash_at_end:
        if self.db.put_dir(path):
          ret = "PUT: dirctory %s is created." % full_path
          status_code = 201
        else:
          ret = "PUT: directory %s is failed." % full_path
          status_code = 403
      else:
        if self.db.put_file(path, content):
          ret = "PUT: file %s is created." % full_path
          status_code = 201
        else:
          ret = "PUT: file %s is failed." % full_path
          status_code = 403

    elif http_method == "UPDATE":
      if type is self.db.FILE:
        if self.db.update_file(path, content):
          ret = "UPDATE: file %s is updated." % full_path
          status_code = 200
        else:
          ret = "UPDATE: file %s is failed." % full_path
          status_code = 403
      else:
        ret = "UPDATE: %s is not a file." % full_path
        status_code = 403

    elif http_method == "DELETE":
      if type is self.db.DIR:
        if self.db.delete_dir(path):
          ret = "DELETE: directory %s is deleted." % full_path
          status_code = 200
        else:
          ret = "DELETE: directory %s is failed." % full_path
          status_code = 403
      elif type is self.db.FILE:
        if self.db.delete_file(path):
          ret = "DELETE: file %s is deleted." % full_path
          status_code = 200
        else:
          ret = "DELETE: file %s is failed." % full_path
          status_code = 403
      elif type is self.db.NOT_EXIST:
        ret = "DELETE: file %s is not found." % full_path
        status_code = 404
      else:
        ret = "DELETE: type %d of path %s is not supported." % (type, full_path)
        status_code = 501

      """ TODO:
      elif http_method == "POST":
        if type is self.db.DIR:
          ret = self.db.post_dir(path, content)
        else:
          ret = self.db.EXISTED
      """
    else:
      status_code = 400
      ret = "The HTTP method %s is not supported." % http_method

    return (status_code, ret)
