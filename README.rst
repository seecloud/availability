Cloud Services Availability
===========================

Query clouds services, save their availability data
and provide aggregated information via RESTful API

Configuration
=============

Default location of configuration file is */etc/oss/availability/config.json*.

If there is an environment variable *AVAILABILITY_CONF* set, it is used as priority.
In this case it is important to use absolute path to configuration file.

Example:

.. code-block::

    export AVAILABILITY_CONF=/home/username/oss_configs/availability.json
    python availability/main.py

Configuration File Description
------------------------------

Configuration file is plain JSON document which defines
`Flask <http://flask.pocoo.org>`_, connection to data storage and
services quering configuration:

Here is a simple example:

.. code-block::

  {
      "backend": {
          "type": "elastic",
          "connection": [{"host": "127.0.0.1", "port": 9200}]
      },
      "period": 60,
      "regions": [
          {
              "name": "west-1",
              "services": [
                  {"name": "nova", "url": "http://foo.example.org:1234/"},
                  {"name": "cinder", "url": "http://foo.example.org:4567/"}
              ]
          },
          {
             "name": "west-2",
             "services": [
                 {"name": "keystone", "url": "http://example.org/ab/"},
                 {"name": "cinder", "url": "http://example.org/cd/"}
             ]
          }
      ],
      "connection_timeout": 1,
      "read_timeout": 10,
      "logging": {
          "level": "ERROR"
      }
  }

flask
~~~~~

Flask configuration is set via *flask* key and described in
`official documentation <http://flask.pocoo.org/docs/0.11/config/>`_.

The only extra options are *HOST* and *PORT*.

backend
~~~~~~~

Type of backend (currently only "elastic" is supported).
Connection to backend (a list of dicts with host and port keys of
`Elasticsearch <https://github.com/elastic/elasticsearch>`_)

period
~~~~~~

Period of services availability check, in seconds. Numeric.

regions
~~~~~~~

List of services to check, by regions. Each item is an object with
the following properties:

* *name* - region name
* *services* - list of services:

 * *name* - service name
 * *url* - service URL to check

connection_timeout
~~~~~~~~~~~~~~~~~~

Number of seconds to wait until connection is established

read_timeout
~~~~~~~~~~~~

Number of seconds for reading connection response

logging
~~~~~~~

Logging configuration:

* *level* - set specific logging level

Build Docker Image
~~~~~~~~~~~~~~~~~~

To build the image run the following command:

.. code-block:: sh

    docker build -t availability:latest .

Run Docker Containers
~~~~~~~~~~~~~~~~~~~~~

Edit configuration file in-place in the repository:

.. code-block:: sh

    cd ~/availability/
    cp etc/sample_config.json etc/config.json
    vim etc/config.json

Then run two separate containers with applications:

    docker run -d --name avail-watcher -v $PWD/etc:/etc/availability availability availability-watcher
    docker run -d --name avail-api -v $PWD/etc:/etc/availability -p 5010:5000 availability ./entrypoint-api.sh

Or one all-in-one:

    docker run -d --name avail -v $PWD/etc:/etc/availability -p 5010:5000 availability ./entrypoint-all.sh
