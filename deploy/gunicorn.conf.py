# Gunicorn configuration — /home/vigilar/app/deploy/gunicorn.conf.py

bind = "127.0.0.1:8000"
workers = 3          # regra: 2 * núcleos + 1
worker_class = "sync"
timeout = 120
keepalive = 5

# Logs vão para stdout/stderr (capturado pelo systemd)
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
