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
        return ("application/json", json.dumps(content))
      else:
        return ("application/json", json.dumps({
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
      else:
        content_type = 'text/html'
        ret = content
      return (content_type, ret)
