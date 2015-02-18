#!/usr/bin/python

import db
import rest
import unittest

class MockDb(db.Db):

  def __init__(self):
    self.objs = {
      "": (db.Db.DIR, [("a")]),
      "a": (db.Db.DIR, [("a/5566", ), ("a/183", ), ]),
      "a/183": (db.Db.FILE, "183 club"),
      "a/5566": (db.Db.FILE, "Asian god group: 5566"),
      "not_exist": (db.Db.NOT_EXIST, None),
    }
    self.htpasswd = {
      "/a": "5566",
      "/a/183": "pass183",
      "/a/5566": "pass5566",
      "/nobody": "passwd",
    }

  def path_type(self, path):
    p = "/".join(path)
    if p in self.objs:
      return self.objs[p][0]

    return db.Db.NOT_EXIST

  def get_dir(self, path):
    p = "/".join(path)
    if p in self.objs and self.objs[p][0] is self.DIR:
      return self.objs[p][1]
    return None

  def get_file(self, path):
    p = "/".join(path)
    if p in self.objs and self.objs[p][0] is self.FILE:
      return self.objs[p][1]
    return None

  def put_dir(self, path):
    p = "/".join(path)
    if p in self.objs:
      return False
    self.objs[p] = (db.Db.DIR, p)
    return True

  def put_file(self, path, content):
    p = "/".join(path)
    if p in self.objs:
      return False
    self.objs[p] = (db.Db.FILE, content)
    return True

  def update_file(self, path, content):
    p = "/".join(path)
    if p not in self.objs:
      return False
    self.objs[p] = (db.Db.FILE, content)
    return True

  def dir_is_empty(self, path):
    for p in self.objs.keys():
      if p is not path and p.startswith(path):
        return False
    return True

  def delete_dir(self, path):
    p = "/".join(path)
    if p in self.objs and self.dir_is_empty(p):
      del self.objs[p]
      return True
    return False

  def delete_file(self, path):
    p = "/".join(path)
    if p in self.objs:
      del self.objs[p]
      return True
    return False

  """ TODO
  def post_dir(self, path):
    new_file = "%08d" % self.serial
    self.serial = self.serial + 1
    path.append(new_file)
    p = "/".join(path)
    self.objs[p] = (db.Db.FILE, "new file: %s" % new_file)
    return p
  """

  def need_authentication(self, path):
    return path in self.htpasswd

  def get_password(self, userpath):
    if userpath in self.htpasswd:
      return self.htpasswd[userpath]
    else:
      return None


class TestDb(unittest.TestCase):

  def test_existing(self):
    db = MockDb()
    r = rest.Rest(db)
    (status_code, ret) = r.handle("GET", "")
    self.assertListEqual(ret, db.objs[""][1], "GET ROOT error")
    (status_code, ret) = r.handle("GET", "a")
    self.assertListEqual(ret, db.objs["a"][1], "GET a error")
    (status_code, ret) = r.handle("GET", "a/5566")
    self.assertEqual(ret, db.objs["a/5566"][1], "GET a/5566 error")
    (status_code, ret) = r.handle("GET", "a/183")
    self.assertEqual(ret, db.objs["a/183"][1], "GET a/183 error")

  def test_not_existing(self):
    db = MockDb()
    r = rest.Rest(db)
    (status_code, ret) = r.handle("GET", "not_exist")
    self.assertEqual(status_code, 404)
    """ TODO:
    (status_code, ret) = r.handle("POST", "")
    self.assertEqual(ret, "/00000000")
    (status_code, ret) = r.handle("POST", "a")
    self.assertEqual(ret, "a/00000001")
    """

  def test_put(self):
    db = MockDb()
    r = rest.Rest(db)
    (status_code, ret) = r.handle("PUT", "put/dir/")
    self.assertEqual(status_code, 201)
    (status_code, ret) = r.handle("GET", "put/dir/")
    self.assertEqual(status_code, 200)
    (status_code, ret) = r.handle("PUT", "put/dir/file")
    self.assertEqual(status_code, 201)
    (status_code, ret) = r.handle("GET", "put/dir/file")
    self.assertEqual(status_code, 200)

  def test_update(self):
    db = MockDb()
    r = rest.Rest(db)
    (status_code, ret) = r.handle("UPDATE", "a")
    self.assertEqual(status_code, 403)
    (status_code, ret) = r.handle("UPDATE", "not_exist")
    self.assertEqual(status_code, 403)
    (status_code, ret) = r.handle("UPDATE", "a/183", {"content": ["183"]})
    self.assertEqual(status_code, 200)
    (status_code, ret) = r.handle("GET", "a/183")
    self.assertEqual(status_code, 200)
    self.assertEqual(ret, "183")

  def test_delete(self):
    db = MockDb()
    r = rest.Rest(db)
    (status_code, ret) = r.handle("DELETE", "a/5566");
    self.assertEqual(status_code, 200)
    (status_code, ret) = r.handle("GET", "a/5566")
    self.assertEqual(status_code, 404)

    (status_code, ret) = r.handle("DELETE", "a")
    self.assertEqual(status_code, 403)

    (status_code, ret) = r.handle("DELETE", "a/183");
    self.assertEqual(status_code, 200)
    (status_code, ret) = r.handle("DELETE", "a")
    self.assertEqual(status_code, 200)

  def test_can_access(self):
    db = MockDb()
    r = rest.Rest(db)
    
    # For those directories not requiring permission.
    self.assertTrue(r.can_access(None, "/nonexist"))
    self.assertTrue(r.can_access(None, "/"))
    self.assertTrue(r.can_access("/nobody", "/nonexist"))

    # For those directories you have access right.
    self.assertTrue(r.can_access("/a", "/a"))
    self.assertTrue(r.can_access("/a/183", "/a/183"))
    self.assertTrue(r.can_access("/a/5566", "/a/5566"))
    self.assertTrue(r.can_access("/a", "/a/183"))
    self.assertTrue(r.can_access("/a", "/a/5566"))
    self.assertTrue(r.can_access("/a", "/a/7788"))
    self.assertTrue(r.can_access("/a", "/a/183/club"))
    self.assertTrue(r.can_access("/a", "/a/5566/GodBand"))

    # You don't have access right.
    self.assertFalse(r.can_access("/a/183", "/a/5566"))
    self.assertFalse(r.can_access("/nobody", "/a/183"))
    self.assertFalse(r.can_access("/a/183/club", "/a"))
    self.assertFalse(r.can_access("/a/183/club", "/a/183"))
    self.assertFalse(r.can_access("/a/5566/GodBand", "/a/183"))


if __name__ == '__main__':
  unittest.main()
