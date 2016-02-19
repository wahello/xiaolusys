#pidfile='/var/www/deploy/taobao/gunicorn.pid'
#daemon=True
import multiprocessing

workers=multiprocessing.cpu_count() * 2 + 1
bind="0.0.0.0:9000"

timeout=20
worker_connections=multiprocessing.cpu_count() * 400 #all worker handle max connects a time
#The maximum number of requests a worker will process before restarting.
#This is a simple method to help limit the damage of memory leaks
max_requests=1000 
#The maximum number of pending connections.
#Exceeding this number results in the client getting an error when attempting to connect. 
#It should only affect servers under significant load.
backlog=multiprocessing.cpu_count() * 400 

#accesslog='/var/log/taobao/gunicorn.out'
#access_log_format="%(h)s %(l)s %(t)s %(r)s %(l)s %(s)s %(l)s %(b)s %(l)s %(D)s "
#access_log_format="%(h)s %(l)s %(u)s %(t)s %(r)s %(s)s %(b)s %(f)s %(a)s"
errorlog='/var/log/taobao/gunicorn.err' 
loglevel='error'
  
