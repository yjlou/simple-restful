#!/usr/bin/python

import db
import os
import shutil
import tempfile

DEBUG = 4

class FileSystem(db.Db):

  root = None  # Root directory
  serial = 0   # For POST to creste new file

  def __init__(self, root):
    self.root = root

  def path_type(self, path):
    path = "%s/%s" % (self.root, self.safe_path(path))
    if os.path.isfile(path):
      return db.Db.FILE
    if os.path.isdir(path):
      return db.Db.DIR
    return db.Db.NOT_EXIST

  def get_dir(self, path):
    path = "%s/%s" % (self.root, self.safe_path(path))
    items = sorted(os.listdir(path))
    ret = []
    for i in items:
      if i[0] == ".":
        continue

      p = "%s/%s" % (path, i)
      if os.path.isfile(p):
        ret.append({"type": db.Db.FILE, "name": i})
      elif os.path.isdir(p):
        ret.append({"type": db.Db.DIR, "name": i})

    return ret

  def get_file(self, path):
    path = "%s/%s" % (self.root, self.safe_path(path))
    return open(path, "r").read()

  def get_last_modified(self, path):
    path = "%s/%s" % (self.root, self.safe_path(path))
    return os.path.getctime(path)

  def put_dir(self, path):
    path = "%s/%s" % (self.root, self.safe_path(path))
    try:
      os.mkdir(path)
    except OSError:
      return False
    return True

  # share code with update_file()
  def put_file(self, path, content):
    path = "%s/%s" % (self.root, self.safe_path(path))
    # If the path has been existed and is a directory, return error.
    if os.path.isdir(path):
      return False

    # Write content to a temp file, then move to target (for atomic).
    #
    try:
      with tempfile.NamedTemporaryFile(delete = False) as fp:
        fp.write(content)
        fp.close()
        shutil.move(fp.name, path)
    except IOError:
      return False
    return True

  def update_file(self, path, content):
    return self.put_file(path, content)

  def delete_file(self, path):
    path = "%s/%s" % (self.root, self.safe_path(path))
    try:
      os.remove(path)
    except OSError:
      return False
    return True

  def delete_dir(self, path):
    path = "%s/%s" % (self.root, self.safe_path(path))
    try:
      os.rmdir(path)
    except OSError:
      return False
    return True

  """
  def post_dir(self, path, content):
    new_file = "%08d" % self.serial  # TODO: use random
    self.serial = self.serial + 1
    path.append(new_file)

    path = "%s/%s" % (self.root, self.safe_path(path))
    with open(path, "w") as fp:
      fp.write(content)
    return True
  """

  def htpasswd_filename(self, path):
    return "/".join([self.root] + [path] + [".htpasswd"])

  def has_htpasswd(self, path):
    return os.path.isfile(self.htpasswd_filename(path))

  def open_htpasswd(self, path):
    htpasswd = self.htpasswd_filename(path)
    if os.path.isfile(htpasswd):
      return open(htpasswd, "r")
    else:
      return open("/dev/null", "r")

  def need_authentication(self, path):
    pathes = self.safe_path(path.split("/")).split("/")
    while len(pathes) > 0:
      if self.has_htpasswd("/".join(pathes)):
        if self.get_password("/".join(pathes + ["*"])) == "":
          return False
        return True
      pathes.pop()
    return False

  def get_password(self, userpath):
    if DEBUG >= 5: print "userpath: ", userpath
    assert userpath

    userpathes = userpath.split("/")
    username = userpathes.pop() if len(userpathes) else None
    pathes = self.safe_path(userpathes).split("/")

    while pathes is not None:

      path = "/".join(pathes)
      if len(pathes) == 0:
        pathes = None
      else:
        pathes.pop()

      if not self.has_htpasswd(path):
        # The .htpasswd file is not found, try parent directory.
        if DEBUG >= 5: print "not self.has_htpasswd()"
        continue

      with self.open_htpasswd(path) as fp:
        for line in fp:
          entries = line.rstrip().split(":")
          user = entries[0]
          password = entries[1]
          if user == username:
            return password

        # Not authorized to access.
        return None

    # No authentication is required.
    return ""
