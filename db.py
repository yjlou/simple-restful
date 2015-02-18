#!/usr/bin/python
#
# I'm interface. Don't import me directly.

class Db():

  EXISTED = -2    # Only used for create new file/directory.
  NOT_EXIST = -1
  DIR = 1
  FILE = 2

  def safe_path(self, path):
    return "/".join([p for p in path if len(p) and p[0] != "."])

  def get_dir(self, path):
    raise Exception("Please implement Db.get)dir()")

  def get_file(self, path):
    raise Exception("Please implement Db.get_file()")

  # Returns the timestamp value (seconds, in GTM)
  def get_last_modified(self, path):
    raise Exception("Please implement Db.get_last_modified()")

  def put_dir(self, path):
    raise Exception("Please implement Db.put_dir()")

  def put_file(self, path):
    raise Exception("Please implement Db.put_file()")

  def updatefile(self, path):
    raise Exception("Please implement Db.update_file()")

  def delete_dir(self, path):
    raise Exception("Please implement Db.delete_dir()")

  def delete_file(self, path):
    raise Exception("Please implement Db.delete_file()")

  def post_file(self, path):
    raise Exception("Please implement Db.post_file()")

  def need_authentication(self, path):
    """
    Return if the path requires user to authenticate itself.
    """
    raise Exception("Please implement Db.need_authentication()")

  def get_password(self, userpath):
    """
    Return the password for the userpath.

    Return:
      None   -- This user is not in the access list (not authorized).
      ""     -- No authenticate is required for this directory.
      string -- User's plaintext password.
    """
    raise Exception("Please implement Db.get_password()")
