#!/bin/bash

availability-watcher &
gunicorn -w 4 -b 0.0.0.0:5000 availability.main:app &

wait -n
