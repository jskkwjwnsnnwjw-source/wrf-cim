#!/usr/bin/env python3
"""
Download de dados ECMWF Open Data para CIM WRF 3 KM
Fonte: https://data.ecmwf.int/forecasts/
Não requer API key (dados abertos)

Uso:
    python3 download_ecmwf.py -i "2024-01-15T12:00:00Z" -f "0,3,6,9,12" -o ./ecmwf_data
"""

import argparse
import os
import sys
import requests
from datetime import datetime, timedelta

def parse_args():
    parser = argparse.ArgumentParser(description='Download ECMWF Open Data')
    parser.add_argument('-i', '--init-time', required=True, help='Initial time (ISO format: YYYY-MM-DDTHH:MM:SSZ)')
    parser.add_argument('-f', '--forecast-hours', required=True, help='Forecast hours comma-separated (e.g., 0,3,6,9,12)')
    parser.add_argument('-o', '--output-dir', default='./ecmwf_data', help='Output directory')
    parser.add_argument('-t', '--test-mode', action='store_true', help='Test mode: only check availability, do not download')
    return parser.parse_args()

def get_ecmwf_url(init_time_str, forecast_hour):
    """Gerar URL para arquivo ECMWF Open Data"""
    init_time = datetime.fromisoformat(init_time_str.replace('Z', '+00:00'))
    date_str = init_time.strftime('%Y%m%d')
    hour_str = init_time.strftime('%H')
    forecast_hour_str = f"{forecast_hour:03d}"
    
    base_url = "https://data.ecmwf.int/forecasts"
    filename = f"{date_str}{hour_str}0000-{forecast_hour_str}h-oper-fc.grib2"
    
    url = f"{base_url}/{date_str}/{hour_str}z/ifs/0p25/oper/{filename}"
    return url

def check_availability(url):
    """Verificar se o arquivo está disponível (HEAD request)"""
    try:
        response = requests.head(url, timeout=30)
        return response.status_code == 200
    except requests.RequestException:
        return False

def download_file(url, output_path):
    """Baixar arquivo com progress bar"""
    print(f"[ECMWF] Downloading: {url}")
    
    response = requests.get(url, stream=True, timeout=300)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0
    
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\r[ECMWF] Progress: {percent:.1f}% ({downloaded/1024/1024:.1f} MB)", end='', flush=True)
    
    print()
    return True

def main():
    args = parse_args()
    forecast_hours = [int(h.strip()) for h in args.forecast_hours.split(',')]
    os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"[ECMWF] Initial time: {args.init_time}")
    print(f"[ECMWF] Forecast hours: {forecast_hours}")
    print(f"[ECMWF] Output directory: {args.output_dir}")
    print()
    
    print("[ECMWF] Checking availability...")
    available_files = []
    
    for hour in forecast_hours:
        url = get_ecmwf_url(args.init_time, hour)
        if check_availability(url):
            available_files.append((hour, url))
            print(f"[ECMWF] OK F{hour:03d}")
        else:
            print(f"[ECMWF] FAIL F{hour:03d}")
    
    if not available_files:
        print("[ECMWF] ERRO: Nenhum arquivo disponivel.")
        sys.exit(1)
    
    if args.test_mode:
        print("\n[ECMWF] TEST MODE: Skipping download.")
        print("[ECMWF] SUCESSO")
        sys.exit(0)
    
    print("\n[ECMWF] Starting download...")
    downloaded_count = 0
    
    for hour, url in available_files:
        filename = os.path.basename(url)
        output_path = os.path.join(args.output_dir, filename)
        
        try:
            download_file(url, output_path)
            downloaded_count += 1
            print(f"[ECMWF] OK: {filename}")
        except Exception as e:
            print(f"[ECMWF] FAIL {filename}: {e}")
    
    print()
    print("=" * 50)
    print(f"[ECMWF] Completed: {downloaded_count}/{len(available_files)} files")
    if downloaded_count == len(available_files):
        print("[ECMWF] SUCESSO")
        sys.exit(0)
    else:
        print("[ECMWF] AVISO: Alguns downloads falharam")
        sys.exit(1)

if __name__ == '__main__':
    main()
