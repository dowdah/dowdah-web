import multiprocessing

# Adjusted worker count for Raspberry Pi
workers = max(2, multiprocessing.cpu_count())

# Bind to all interfaces on port 5000
bind = '0.0.0.0:5000'

# Retain 'gevent' for efficient handling of connections
worker_class = 'gthread'

# Adjusted log level to minimize I/O on Raspberry Pi
accesslog = '-'
errorlog = '-'
loglevel = 'warning'

# Reduced backlog to avoid excessive pending connections
backlog = 256

# Increased max requests before worker restart to reduce overhead
max_requests = 5000
max_requests_jitter = 500

# Timeouts and keepalive settings retained
timeout = 30
keepalive = 2
