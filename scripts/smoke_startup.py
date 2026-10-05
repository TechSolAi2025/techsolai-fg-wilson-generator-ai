"""Repeat a real localhost Streamlit HTTP startup; stop only the child processes created here."""
import argparse,json,os,re,socket,subprocess,sys,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--report-tag',default='')
    tag=parser.parse_args().report_tag
    if tag and not re.fullmatch(r'[a-z0-9_]+',tag):parser.error('invalid report tag')
    suffix='_'+tag if tag else ''
    results=[]
    for attempt in range(2):
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        logpath=ROOT/f'exports/startup_{attempt+1}{suffix}.log'
        with logpath.open('w',encoding='utf-8') as log:
            start=time.perf_counter()
            proc=subprocess.Popen([sys.executable,'-m','streamlit','run','app/streamlit_app.py','--global.developmentMode=false','--server.headless=true','--server.address=127.0.0.1',f'--server.port={port}','--browser.gatherUsageStats=false'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            try:
                success=False
                while time.perf_counter()-start<25:
                    if proc.poll() is not None: break
                    try:
                        with urllib.request.urlopen(f'http://127.0.0.1:{port}/_stcore/health',timeout=1) as response:
                            if response.status==200 and response.read()==b'ok':success=True;break
                    except OSError:pass
                    time.sleep(.2)
                results.append({'attempt':attempt+1,'http_health':success,'startup_seconds':time.perf_counter()-start,'port':port})
            finally:
                proc.terminate()
                try:proc.wait(timeout=10)
                except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
    (ROOT/f'exports/startup_smoke{suffix}.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps(results));return 0 if all(r['http_health'] for r in results) else 1
if __name__=='__main__':raise SystemExit(main())
