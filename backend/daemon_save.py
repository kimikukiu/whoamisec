#!/usr/bin/env python3
"""
Daemonize WHOAMISecAI Agentic AI Service on port 5010.
Double-fork pattern for VPS container survival.
"""

import os
import sys

def daemonize():
    # First fork
    pid = os.fork()
    if pid > 0:
        sys.exit(0)

    # Decouple from parent environment
    os.chdir('/home/z/my-project/whoamisec-repo/backend')
    os.setsid()

    # Second fork
    pid = os.fork()
    if pid > 0:
        sys.exit(0)

    # Redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()
    with open('/dev/null', 'r') as devnull:
        os.dup2(devnull.fileno(), sys.stdin.fileno())
    log_path = '/home/z/my-project/whoamisec-repo/backend/agentic_service.log'
    with open(log_path, 'a') as log:
        os.dup2(log.fileno(), sys.stdout.fileno())
        os.dup2(log.fileno(), sys.stderr.fileno())

    # Write PID file
    with open('/home/z/my-project/whoamisec-repo/backend/agentic_service.pid', 'w') as f:
        f.write(str(os.getpid()))

    # Start the service
    os.environ['AGENTIC_PORT'] = '5010'
    os.environ['PYTHONPATH'] = '/home/z/my-project/whoamisec-repo/backend'
    os.execl('/usr/bin/python3', '/usr/bin/python3', 'agentic_ai_service.py')

if __name__ == '__main__':
    daemonize()
