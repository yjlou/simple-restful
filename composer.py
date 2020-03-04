#!/usr/bin/python

from types import *
import db
import json

class Composer():

  def __init__(self, output_format, db):
    self.output_format = output_format
    self.db = db

  def compose(self, content, path):
    if self.output_format == "JSON":
      if type(content) is ListType:  # directory list, DIR
        return ("application/json; charset=UTF-8", json.dumps(content))
      else:
        return ("application/json; charset=UTF-8", json.dumps({
          "content": content,
          "last_modified": self.db.get_last_modified(path.split("/")),
        }))
    else:
      if type(content) is ListType:  # directory list, DIR
        ret = "<HTML><BODY><UL>"
        for entry in content:
          if entry["type"] == db.Db.DIR:
            name = entry["name"] + "/"
          else:
            name = entry["name"]

          if path[-1] != "/":
            path = path + "/"

          link = "%s%s" % (path, entry["name"])
          ret = ret + "<LI><A HREF='%s'>%s</A>" % (link, name)
        ret = ret + "</UL></BODY></HTML>"
        content_type = 'text/html'
      # TODO: Use magic lib to tell the MIME type.
      elif content.startswith('\xff\xd8\xff\xe0\x00\x10\x4a\x46\x49\x46'):
        content_type = 'image/jpeg'
        ret = content
      elif content.startswith('\x00\x00\x00\x20\x66\x74\x79\x70\x69'):
        content_type = 'video/mp4'
        ret = content
      elif content.startswith('\x52\x49\x46\x46'):
        content_type = 'video/avi'
        ret = content
      elif content.startswith('\x89\x50\x4e\x47\x0d\x0a'):
        content_type = 'image/png'
        ret = content
      elif path.endswith('.css'):
        content_type = 'text/css'
        ret = content
      else:
        content_type = 'text/html'
        ret = content
      return (content_type, ret)
