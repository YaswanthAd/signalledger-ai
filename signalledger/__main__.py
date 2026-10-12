import argparse
import json
from pathlib import Path
from .models import Investigation
from .engine import investigate

def main():
    parser=argparse.ArgumentParser(description="Run SignalLedger without the web server")
    parser.add_argument('request',type=Path)
    parser.add_argument('--ollama',action='store_true')
    args=parser.parse_args()
    try:
        body=json.loads(args.request.read_text())
        if args.ollama:body['analyst']='ollama'
        result=investigate(Investigation.model_validate(body))
        print(json.dumps(result,indent=2,allow_nan=False))
    except (OSError,ValueError) as exc:
        parser.error(str(exc))

if __name__=='__main__':main()
