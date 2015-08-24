Deployments
===========

There is a large number of ways available to deploy a Flask, or rather any
WSGI_ application. This document describes and recommends a particular way of
doing so, which sets the following goals:

* Secure, out of the box. Default configuration may not be the apex of what is
  is possible performance wise, but will be as hardened as possible.
* Grows with the application, like Flask: Small application run almost
  instantly without much extra setup while applications that require extra
  performance are easy to configure and reuse these components.
* Minimal moving parts: As few as possible additional dependencies are
  introduced, to keep the stack small and easy to manage.

.. _WSGI: http://wsgi.readthedocs.org/

Small- to medium scale deployments
----------------------------------

(To be written)


Larger deployments
------------------

(To be written)


A word on systemd
-----------------

(To be written)
