"""Global event handlers.

3 Hooks are provided for each request:

+ pre-hook: called before the request is being run.
+ post-hook: called after the request is done.
+ notify-hook: called after post-hook (async).

Pre-hook and post-hook are blocking, which means the request wouldn't run until
pre-hook is done, post-hook wouldn't run until request is done, and the
response doesn't go back to client until post-hook is completed. Thus, pre-hook
and post-hook should be very light-weighted to reduce the latency.

However, the notify-hook is called asynchronously, which is designed for long-
run batch process. Therefore, the number of notify-hook invocation can be less
than the number of request.

"""
# TODO(P2): implement directory based event handlers.

def PUT_pre(from_root, path_name, content, params=None):
  """Before file is stored, run this function.

  Args:
    from_root: always "" now.
    path_name: the path name to be uploaded.
    content: the content of file.
    params: other parameters in URI.

  Returns:
    False if refuses to store this file/directory.
  """
  # TODO(P1): implement this.
  pass

def PUT_post(from_root, path_name, content, params=None):
  """After file is stored, run this function.

  Args:
    from_root: always "" now.
    path_name: the path name has been updated.
    content: the content of file.
    params: other parameters in URI.
  """
  # TODO(P1): implement this.
  pass

def PUT_notify(from_root, path_name, private):
  """Called after post-hook. For long-run process.

  Args:
    from_root: always "" now.
    path_name: the path name has been updated.
    private: the state returned in the last invocation.

  Returns:
    None or any object. Will be passed in 'private' parameter in the next
    invocation.
  """
  # TODO(P1): implement this.
  pass

