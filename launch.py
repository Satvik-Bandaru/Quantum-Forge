"""Double-click launcher: open an existing lab or run the loopback service."""
import json
import os
import threading
import time
import urllib.request
import webbrowser

URL='http://127.0.0.1:8777'

def ready():
    try:
        with urllib.request.urlopen(URL+'/api/health',timeout=1) as response:
            return json.load(response).get('app')=='quantum-forge-lab'
    except Exception:
        return False


def open_when_ready():
    for _ in range(60):
        if ready():
            webbrowser.open(URL)
            return
        time.sleep(.25)


if __name__=='__main__':
    if ready():
        webbrowser.open(URL)
    else:
        for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
            os.environ.setdefault(key,'1')
        threading.Thread(target=open_when_ready,daemon=True).start()
        import uvicorn
        uvicorn.run('backend.app:app',host='127.0.0.1',port=8777,workers=1)
