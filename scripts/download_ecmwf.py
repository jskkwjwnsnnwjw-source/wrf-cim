#!/usr/bin/env python3
"""
Download de dados ECMWF usando Open Data público (SEM API KEY).

Fontes: https://data.ecmwf.int/forecasts/

Formato URL:
https://data.ecmwf.int/forecasts/YYYYMMDD/HHZ/ifs/0p25/oper/YYYYMMDDHH0000-HHh-oper-fc.grib2

Exemplo real:
https://data.ecmwf.int/forecasts/20260910/00z/ifs/0p25/oper/20260910000000-0h-oper-fc.grib2

Uso:
    python3 download_ecmwf.py -i "2026-09-10T00:00:00Z" -f "0,3,6" -o ./ecmwf_data -t
"""

import argparse
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
import requests
from typing import List

def build_ecmwf_url(init_time: datetime, forecast_hour: int) -> str:
    """Constrói URL para arquivo GRIB2 completo do ECMWF."""
    base = "https://data.ecmwf.int/forecasts"
    date_str = init_time.strftime('%Y%m%d')
    hour_str = init_time.strftime('%H')
    timestamp = init_time.strftime('%Y%m%d%H%M%S')
    return f"{base}/{date_str}/{hour_str}z/ifs/0p25/oper/{timestamp}-{forecast_hour}h-oper-fc.grib2"

def list_available_files(init_time: datetime) -> List[str]:
    """Lista arquivos .grib2 disponíveis."""
    base = "https://data.ecmwf.int/forecasts"
    date_str = init_time.strftime('%Y%m%d')
    hour_str = init_time.strftime('%H')
    url = f"{base}/{date_str}/{hour_str}z/ifs/0p25/oper/"
    
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            return []
        return re.findall(r'href="([^"]*\.grib2)"', resp.text)
    except Exception as e:
        print(f"[ECMWF] Erro listando: {e}")
        return []

def download_file(url: str, output: Path, test_mode: bool = False) -> bool:
    """Baixa arquivo GRIB2."""
    try:
        head = requests.head(url, timeout=30, allow_redirects=True)
        
        if head.status_code == 404:
            print(f"[ECMWF] ✗ Não encontrado: {os.path.basename(url)}")
            return False
        
        if test_mode:
            size = head.headers.get('content-length', '?')
            mb = float(size)/1e6 if size != '?' else 0
            print(f"[ECMWF] ✓ Disponível: {os.path.basename(url)} ({mb:.1f} MB)")
            return True
        
        print(f"[ECMWF] ↓ {os.path.basename(url)}")
        resp = requests.get(url, timeout=600, stream=True)
        resp.raise_for_status()
        
        total = int(resp.headers.get('content-length', 0))
        done = 0
        with open(output, 'wb') as f:
            for chunk in resp.iter_content(8192):
                if chunk:
                    f.write(chunk)
                    done += len(chunk)
                    if total:
                        print(f"\r[ECMWF]   {done/total*100:.1f}%", end='')
        
        print(f"\n[ECMWF] ✓ {output.name} ({done/1e6:.1f} MB)")
        return True
    except Exception as e:
        print(f"\n[ECMWF] ✗ Erro: {e}")
        return False

def main():
    p = argparse.ArgumentParser(description='Download ECMWF Open Data')
    p.add_argument('-i', '--init-time', required=True)
    p.add_argument('-f', '--hours', default='0,3,6,9,12,15,18,21,24,27,30,33,36')
    p.add_argument('-o', '--output-dir', default='./ecmwf_data')
    p.add_argument('-t', '--test-mode', action='store_true')
    args = p.parse_args()
    
    try:
        init = datetime.fromisoformat(args.init_time.replace('Z', '+00:00'))
    except ValueError as e:
        print(f"[ECMWF] ✗ Erro: {e}")
        sys.exit(1)
    
    hstr = args.hours
    hours = list(range(int(hstr.split('-')[0]), int(hstr.split('-')[1])+1, 3)) if '-' in hstr and ',' not in hstr else [int(x.strip()) for x in hstr.split(',')]
    
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}\n[ECMWF] Init: {init.strftime('%Y-%m-%d %H:%M UTC')}\n[ECMWF] Hours: {hours}\n[ECMWF] Test: {args.test_mode}\n{'='*60}\n")
    
    # Listar disponíveis
    print("[ECMWF] Verificando disponibilidade...")
    avail = list_available_files(init)
    if avail:
        print(f"[ECMWF] {len(avail)} arquivos encontrados")
    
    # Download
    ok = True
    for h in hours:
        url = build_ecmwf_url(init, h)
        fname = f"ECMF_{init.strftime('%Y%m%d_%H')}_{h:03d}h_oper.grib2"
        if not download_file(url, outdir/fname, args.test_mode):
            ok = False
    
    print(f"\n{'='*60}\n[ECMWF] {'✓ SUCESSO' if ok or args.test_mode else '✗ FALHA'}\n{'='*60}\n")
    sys.exit(0 if ok or args.test_mode else 1)

if __name__ == '__main__':
    main()
