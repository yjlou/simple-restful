Simple RESTful server implemented by Python. Store data in filesystem. Support HTTP digest authentication. Support HTTPS.

# Highlights

* Implemented in Python
* Data stored in regular filesystem. No database required.
* Possible to extend to use various database.
* Support RESTful commands
* Support HTTPS
* Support HTTP digest authentication

# Supported HTTP Methods

You could use "action={METHOD]" if your HTTP client doesn't support RESTful.

* GET     : retrieve file content or list directory
* POST    : create a new file/dir where the server decides the name (not yet)
* PUT     : create a new file/dir where the client decides the name
* UPDATE  : update the content of an existing file
* DELETE  : delete a file or dir

# Authentication and Authorization:

It employs the HTTP digest authentication.

The username is designed to map with the URI path. For example, to access
the resources under /scaler/4d-5e-1f-43, you should login with the username:

> "/scaler/4d-5e-1f-43" or "/scaler"

Once authenticated, the user has full access to "/scaler/4d-5e-1f-43", the
directory itself, and all files and sub-directories under it.

If you login with username "/scaler", you could access all files/sub-directories
under /scaler. This is useful for administration.

How the secrets are stored?  Take FileSystem(fs.py) for example:

/scaler/.htpasswd contains all accounts for the level of /scalers. In this case,
the .htpasswd contains the username and password of "4d-5e-1f-43":

> 4d-5e-1f-43:plain_text_password_1
> 4d-5e-1f-57:plain_text_password_2
> 4d-5e-1f-6f:plain_text_password_3

There may be a /scalers/4d-5e-1f-43/.htpasswd file. If there is, it contains
the special accounts for that directory.

/.htpasswd only contains the global accounts (i.e. SUPER_ADMIN).


Examples:

1. Empty /.htpasswd
   No access to root

2. No /.htppasswd
   root is free to access

3. (more...)

# Howto Run Server and Client

> Run in console A:
>   % python httpd.py
> 
> Run in console B:
>   % curl -i -H "Accept: application/json" -X PUT -d "content=ThisIsATest" "http://localhost:8888/test-file"
>   HTTP/1.0 201 Created
>   Server: SimpleHTTP/0.6 Python/2.7.3
>   Date: Wed, 18 Feb 2015 04:07:35 GMT
>   Content-type: application/json
>   
>   {"content": "PUT: file /test is created.", "last_modified": 1424232455.0}
> 
>   % cat root/test-file
>   ThisIsATest
> 
>   % curl -i "http://localhost:8888/test-file"
>   HTTP/1.0 200 OK
>   Server: SimpleHTTP/0.6 Python/2.7.3
>   Date: Wed, 18 Feb 2015 04:15:09 GMT
>   Content-type: text/html
>   Last-Modified: Wed, 18 Feb 2015 04:10:57 GMT
> 
>   ThisIsATest

# For developers

Regression:

> % make test

# TODO List

* .htpasswd stored no-plain-text.
* Presentation:
  * join language: join a directory into a csv file.
  * upload csv file to google docs.
  * draw a diagram from csv file.
* How Content-type: matters for uploading?
  * Since 'content' is binary-safe already, it seems nothing matters.
  * If there is one thing worth to consider, that would be POST method
  * to generate anonymous extension filename (for future download).
* Hooks before and after request.
* Authorization:
  * global accounts, like "SUPER_ADMIN", "SUPER_ADMIN2" ... (w/o heading slash)
  * special accounts under projects, like "/scaler/ADMIN1".
* POST response new created file in Location:.
* Limit longpoll usage in configured path
* longpoll config: max_longpoll_timeout
* Support multi Host: homes
* For web users, use facebook/gmail authentication, instead of HTTP auth.
* more efficient longpoll: monitor a directory -- recursively. 302 Moved.
* zip batch download
* zip batch upload
* suport POST method
* More detailed ACL: limit a particular user to rwx a file/dir.
* Upgrade rest.py to WGSI so that we can use on any Web server.
* RSI (REST Service Interface) -- like CGI, to run server side logic.
* Future plans for other HTTP server:
  * Criteria for HTTP server:
    * Support RESTful methods:
      * GET
      * POST
      * PUT
      * UPDATE
      * DELETE
    * Support HTTP Authentication Digest.
    * Support HTTPS.
  * Candidates (and not):
    * tornado:
      * NOT support UPDATE
      * SSL: http://stackoverflow.com/questions/13471115/how-to-handle-a-request-with-https-protocol-in-tornado
      * HTTP AUTH: http://www.renjie.me/?p=54
