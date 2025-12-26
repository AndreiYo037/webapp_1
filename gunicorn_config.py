# Gunicorn configuration file
import multiprocessing

import os
# Railway requires using PORT environment variable
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
accesslog = "-"
errorlog = "-"
loglevel = "info"


