import os, sys
pid = os.fork()
if pid > 0: sys.exit(0)
os.chdir('/home/z/my-project/zai-proxy')
os.setsid()
pid = os.fork()
if pid > 0: sys.exit(0)
sys.stdout.flush(); sys.stderr.flush()
with open('/dev/null','r') as d: os.dup2(d.fileno(), sys.stdin.fileno())
with open('/home/z/my-project/zai-proxy/proxy.log','a') as l:
    os.dup2(l.fileno(), sys.stdout.fileno())
    os.dup2(l.fileno(), sys.stderr.fileno())
with open('/home/z/my-project/zai-proxy/proxy.pid','w') as f: f.write(str(os.getpid()))
os.execl('/usr/bin/node','/usr/bin/node','server.js')
