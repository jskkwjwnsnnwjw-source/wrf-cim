#!/usr/bin/env python3
"""
Download de dados ICON DWD Open Data para CIM WRF 3 KM
Fonte: https://opendata.dwd.de/weather/nwp/icon/grib/
Dados públicos sem necessidade de API key

Uso:
    python3 download_icon.py -i "2024-01-15T12:00:00Z" -f "0,3,6,9,12" -o ./icon_data
"""

import argparse
import os
import sys
import requests
from datetime import datetime, timedelta

def parse_args():
    parser = argparse.ArgumentParser(description='Download ICON DWD Open Data')
    parser.add_argument('-i', '--init-time', required=True, help='Initial time (ISO format)')
    parser.add_argument('-f', '--forecast-hours', required=True, help='Forecast hours comma-separated')
    parser.add_argument('-o', '--output-dir', default='./icon_data', help='Output directory')
    parser.add_argument('-t', '--test-mode', action='store_true', help='Test mode only')
    return parser.parse_args()

def get_icon_url(init_time_str, forecast_hour):
    """Gerar URL para arquivo ICON DWD"""
    init_time = datetime.fromisoformat(init_time_str.replace('Z', '+00:00'))
    
    # ICON global: grade ~13km, disponível a cada 6h (00,06,12,18)
    # Formato: https://opendata.dwd.de/weather/nwp/icon/grib/YYYYMMDDHH/t_2m_ICON_global_YYYYMMDDHH_000_HHH.grib2.bz2
    
    date_str = init_time.strftime('%Y%m%d')
    hour_str = init_time.strftime('%H')
    forecast_hour_str = f"{forecast_hour:03d}"
    
    base_url = "https://opendata.dwd.de/weather/nwp/icon/grib"
    
    # Variáveis necessárias para WRF
    variables = [
        't_2m',      # Temperatura 2m
        'u_10m',     # Vento U 10m
        'v_10m',     # Vento V 10m
        'rel_hum_2m',# Umidade relativa 2m
        'pres_msl',  # Pressão MSL
        't',         # Temperatura em níveis
        'u',         # Vento U em níveis
        'v',         # Vento V em níveis
        'rel_hum',   # Umidade em níveis
        'gh',        # Altura geopotencial
    ]
    
    urls = []
    for var in variables:
        filename = f"{var}_ICON_global_{date_str}{hour_str}_000_{forecast_hour_str}.grib2.bz2"
        url = f"{base_url}/{date_str}{hour_str}/{filename}"
        urls.append((var, url))
    
    return urls

def check_availability(url):
    try:
        response = requests.head(url, timeout=30)
        return response.status_code == 200
    except requests.RequestException:
        return False

def download_file(url, output_path):
    print(f"[ICON] Downloading: {os.path.basename(url)}")
    
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
                    print(f"\r[ICON] Progress: {percent:.1f}%", end='', flush=True)
    
    print()
    return True

def main():
    args = parse_args()
    forecast_hours = [int(h.strip()) for h in args.forecast_hours.split(',')]
    os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"[ICON] Initial time: {args.init_time}")
    print(f"[ICON] Forecast hours: {forecast_hours}")
    print(f"[ICON] Output directory: {args.output_dir}")
    print()
    
    print("[ICON] Checking availability...")
    all_available = True
    files_to_download = []
    
    for hour in forecast_hours:
        urls = get_icon_url(args.init_time, hour)
        hour_ok = True
        
        for var, url in urls:
            if check_availability(url):
                files_to_download.append((var, hour, url))
            else:
                # Algumas variáveis podem não estar disponíveis em todas as horas
                pass
    
    if not files_to_download:
        print("[ICON] ERRO: Nenhum arquivo disponivel.")
        sys.exit(1)
    
    if args.test_mode:
        print("\n[ICON] TEST MODE: Skipping download.")
        print(f"[ICON] Found {len(files_to_download)} files")
        print("[ICON] SUCESSO")
        sys.exit(0)
    
    print(f"\n[ICON] Starting download ({len(files_to_download)} files)...")
    downloaded_count = 0
    
    for var, hour, url in files_to_download:
        filename = os.path.basename(url)
        output_path = os.path.join(args.output_dir, filename)
        
        try:
            download_file(url, output_path)
            downloaded_count += 1
            print(f"[ICON] OK: {filename}")
        except Exception as e:
            print(f"[ICON] FAIL {filename}: {e}")
    
    print()
    print("=" * 50)
    print(f"[ICON] Completed: {downloaded_count}/{len(files_to_download)} files")
    if downloaded_count == len(files_to_download):
        print("[ICON] SUCESSO")
        sys.exit(0)
    else:
        print("[ICON] AVISO: Alguns downloads falharam")
        sys.exit(1)

if __name__ == '__main__':
    main()
