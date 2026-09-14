import json, os, secrets, subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
ROOT=Path('/workspaces/Minis').resolve()
PORT=int(os.environ.get('PORT','8787'))
TF=Path.home()/'.minis_mcp_token'
TOKEN='3f102320465931a7433ae1d648782a3b39967d2165ac96a3'
else:
 TOKEN=secrets.token_urlsafe(32); TF.write_text(TOKEN); TF.chmod(0o600)
def out(i,result=None,error=None):
 d={'jsonrpc':'2.0','id':i}; d['result' if error is None else 'error']=result if error is None else error; return d
def path(p):
 q=(ROOT/str(p or '.').lstrip('/')).resolve()
 if q!=ROOT and ROOT not in q.parents: raise ValueError('outside workspace')
 return q
def call(n,a):
 a=a or {}
 if n=='shell':
  r=subprocess.run(a['command'],shell=True,cwd=ROOT,text=True,capture_output=True,timeout=min(int(a.get('timeout',120)),300))
  return {'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
 if n=='read_file': return {'path':str(path(a['path'])),'content':path(a['path']).read_text()}
 if n=='write_file':
  q=path(a['path']); q.parent.mkdir(parents=True,exist_ok=True); q.write_text(a.get('content','')); return {'ok':True,'path':str(q)}
 if n=='list_dir': return {'path':str(path(a.get('path','.'))),'entries':sorted(x.name for x in path(a.get('path','.')).iterdir())}
 raise ValueError('unknown tool')
TOOLS=[{'name':'shell','description':'Run a shell command in the Minis workspace.','inputSchema':{'type':'object','properties':{'command':{'type':'string'},'timeout':{'type':'integer'}},'required':['command']}},{'name':'read_file','description':'Read a workspace file.','inputSchema':{'type':'object','properties':{'path':{'type':'string'}},'required':['path']}},{'name':'write_file','description':'Write a workspace file.','inputSchema':{'type':'object','properties':{'path':{'type':'string'},'content':{'type':'string'}},'required':['path','content']}},{'name':'list_dir','description':'List workspace files.','inputSchema':{'type':'object','properties':{'path':{'type':'string'}}}}]
class H(BaseHTTPRequestHandler):
 def log_message(self,*x): pass
 def do_GET(self):
  if self.path in ('/','/health'):
   b=b'{"status":"ok","service":"minis-mcp"}'; self.send_response(200); self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(b)
  else: self.send_error(404)
 def do_POST(self):
  if self.path!='/mcp' or self.headers.get('Authorization')!='Bearer '+TOKEN: self.send_error(401); return
  try:
   x=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0')))); i=x.get('id'); m=x.get('method'); p=x.get('params') or {}
   if m=='initialize': r=out(i,{'protocolVersion':'2025-03-26','capabilities':{'tools':{}},'serverInfo':{'name':'minis-codespace-shell','version':'1.0'}})
   elif m=='notifications/initialized': self.send_response(202); self.end_headers(); return
   elif m=='tools/list': r=out(i,{'tools':TOOLS})
   elif m=='tools/call': r=out(i,{'content':[{'type':'text','text':json.dumps(call(p.get('name'),p.get('arguments')),ensure_ascii=False)}]})
   else: r=out(i,error={'code':-32601,'message':'method not found'})
   b=json.dumps(r).encode(); self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
  except Exception as e: self.send_error(500,str(e))
print('MCP listening on',PORT,flush=True); print('TOKEN_FILE',TF,flush=True); ThreadingHTTPServer(('0.0.0.0',PORT),H).serve_forever()
