#!/usr/bin/python

import db
import fs
import os
import stat
import subprocess
import tempfile
import time
import unittest

DEBUG = 4
ROOT = "test_root/"

class TestDb(unittest.TestCase):

  def setUp(self):
    self.root = tempfile.mkdtemp()
    if DEBUG >= 5:
      print "TestDb.setUp() ... create temp dir: %s" % self.root
    self.assertEqual(0, subprocess.call("cp -r %s* %s" %
                                        (ROOT, self.root), shell = True))
    self.fs = fs.FileSystem(self.root)

  def test_safe_path(self):
    self.assertEqual("", self.fs.safe_path(["."]))
    self.assertEqual("", self.fs.safe_path([".."]))
    """ we trust the / has been handled in rest.py
    self.assertEqual("", self.fs.safe_path(["/.."]))
    self.assertEqual("", self.fs.safe_path(["/../"]))
    self.assertEqual("", self.fs.safe_path(["/../.."]))
    self.assertEqual("", self.fs.safe_path(["/../../"]))
    self.assertEqual("", self.fs.safe_path(["/../../../../"]))
    """

  def test_get_dir(self):
    self.assertListEqual([
      {"type": db.Db.DIR, "name": "noauth"},
      {"type": db.Db.DIR, "name": "uid"},
      {"type": db.Db.DIR, "name": "tests"},
      {"type": db.Db.DIR, "name": "auth"},
      ], self.fs.get_dir([]))

  def test_get_file(self):
    self.assertEqual("I am 5566\n", self.fs.get_file(["uid", "5566"]))

  def test_get_file(self):
    self.assertEqual("I am 5566\n", self.fs.get_file(["uid", "5566"]))

  def test_get_last_modified(self):
    org = self.fs.get_last_modified(["uid", "5566"])
    time.sleep(2)
    os.chmod(self.fs.safe_path([self.root, "uid", "5566"]),
             stat.S_IRUSR | stat.S_IWUSR)
    new = self.fs.get_last_modified(["uid", "5566"])
    self.assertNotEqual(org, new)

  def test_put(self):
    self.assertEqual(True, self.fs.put_dir(["put"]))
    self.assertListEqual([
      {"type": db.Db.DIR, "name": "noauth"},
      {"type": db.Db.DIR, "name": "uid"},
      {"type": db.Db.DIR, "name": "put"},
      {"type": db.Db.DIR, "name": "tests"},
      {"type": db.Db.DIR, "name": "auth"},
      ], self.fs.get_dir([]))

    self.assertEqual(True, self.fs.put_file(["put", "file"], "new_file"))
    self.assertEqual("new_file", self.fs.get_file(["put", "file"]))

  def test_delete(self):
    self.assertEqual(False, self.fs.delete_dir(["uid", "5566"]))
    self.assertEqual(False, self.fs.delete_dir(["uid"]))
    self.assertEqual(True, self.fs.delete_file(["uid", "5566"]))
    self.assertEqual(True, self.fs.delete_dir(["uid"]))

  def test_get_password(self):
    self.assertEqual(self.fs.get_password("/"), "")
    self.assertEqual(self.fs.get_password("/any"), "")
    self.assertEqual(self.fs.get_password("/noauth"), "")
    self.assertEqual(self.fs.get_password("/noauth/any"), "")
    self.assertEqual(self.fs.get_password("/noauth/auth"), "")
    self.assertEqual(self.fs.get_password("/noauth/auth/naFirst"), "na34")
    self.assertEqual(self.fs.get_password("/noauth/auth/naSecond"), "na78")
    self.assertEqual(self.fs.get_password("/noauth/auth/naNonExist"), None)
    self.assertEqual(self.fs.get_password("/noauth/noauth"), "")
    self.assertEqual(self.fs.get_password("/auth"), "")
    self.assertEqual(self.fs.get_password("/auth/aFirst"), "a234")
    self.assertEqual(self.fs.get_password("/auth/aSecond"), "a678")
    self.assertEqual(self.fs.get_password("/auth/auth"), "a456")
    self.assertEqual(self.fs.get_password("/auth/aNonExist"), None)
    self.assertEqual(self.fs.get_password("/auth/noauth/aFirst"), "a234")
    self.assertEqual(self.fs.get_password("/auth/auth/aaFirst"), "aa34")
    self.assertEqual(self.fs.get_password("/auth/auth/aaSecond"), "aa78")
    self.assertEqual(self.fs.get_password("/auth/auth/aaNonExist"), None)
    self.assertEqual(self.fs.get_password("/auth/auth/noauth"), None)
    self.assertEqual(self.fs.get_password("/auth/auth/noauth/aaFirst"), "aa34")
    self.assertEqual(self.fs.get_password("/auth/auth/noauth/any"), None)
    self.assertEqual(self.fs.get_password("/auth/public/*"), "")

if __name__ == '__main__':
  unittest.main()

