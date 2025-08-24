#!/usr/bin/env python3
import re
import os
from datetime import datetime, timedelta
from py_module.config import CONFIG_PATH

NETRUM_FILE = ".netrum"

def parse_log_line(line, claim_after_days=0):
    result={"time":"-","progress":"-","mined":"-","speed":"-","status":"-"}
    line=line.replace('⏱️','').strip()
    parts=[p.strip() for p in line.split('|')]
    for p in parts:
        if re.search(r'\d+h\s*\d+m\s*\d+s',p):
            h,m,s=map(int,re.findall(r'\d+',p))
            result["time"]=f"{h:02d}:{m:02d}:{s:02d}"
        elif p.strip().endswith('%'):
            try:
                percent=float(p.replace('%','').strip())
                bar_len=14
                filled_len=int(bar_len*percent/100)
                result["progress"]='█'*filled_len+'░'*(bar_len-filled_len)+f' {percent:.2f}%'
            except: result["progress"]=p
        elif p.lower().startswith("mined:"):
            try: val=p.split(":",1)[1].strip().split()[0]; result["mined"]=f"{float(val):.6f}"
            except: pass
        elif p.lower().startswith("speed:"): result["speed"]=p.split(":",1)[1].strip()
        elif p.lower().startswith("status:"): result["status"]=p.split(":",1)[1].strip()
    return result