#!/usr/bin/env python3
"""
Download de dados ICON para o CIM WRF 3 KM

URL FORMAT (confirmado):
https://opendata.dwd.de/weather/nwp/icon/grib/{HH}/{var_dir}/icon_global_icosahedral_single-level_{YYYYMMDD}{HH}_{FFF}_{VAR}.grib2.bz2

Exemplo real:
https://opendata.dwd.de/weather/nwp/icon/grib/00/t_2m/icon_global_icosahedral_single-level_2026091000_000_T_2M.grib2.bz2
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import requests


ICON_BASE_URL = "https://opendata.dwd.de/weather/nwp/icon/grib"

CIM_BOUNDS = {
    "north": -15.0,
    "south": -45.0,
    "west": -70.0,
    "east": -42.0
}

# Mapeamento: variável interna -> diretório -> nome no arquivo
ICON_VARIABLES = {
    "single-level": [
        ("t_2m", "t_2m", "T_2M"),
        ("u_10m", "u_10m", "U_10M"),
        ("v_10m", "v_10m", "V_10M"),
        ("pmsl", "pmsl", "PMSL"),
        ("pres_sfc", "pres_sfc", "PRES_SFC"),
    ],
    "pressure-level": [
        ("gh", "geopotential", "GEOPOTENTIAL"),
        ("t", "t", "T"),
        ("u", "u", "U"),
        ("v", "v", "V"),
        ("rh", "relhum", "RELHUM"),
    ]
}

PRESSURE_LEVELS = [
    1000, 975, 950, 925, 900, 850, 800, 750, 700, 650,
    600, 550, 500, 450, 400, 350, 300, 250, 225, 200,
    175, 150, 125, 100, 75, 50, 30, 20, 10
]


def parse_init_time(init_time_str):
    formats = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y%m%d%H"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(init_time_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Formato não reconhecido: {init_time_str}")


def generate_forecast_hours(hours_str):
    if not hours_str:
        return list(range(0, 37, 3))
    return [int(h.strip()) for h in hours_str.split(",")]


def get_icon_url(variable_type, var_dir, var_icon, init_time, forecast_hour, pressure_level=None):
    """Constrói URL baseado no formato REAL do DWD"""
    date_str = init_time.strftime("%Y%m%d")
    hour_str = init_time.strftime("%H")
    
    if pressure_level:
        # Para níveis de pressão, o formato é diferente
        # Ex: icon_global_icosahedral_850level_2026091000_000_GH.grib2.bz2
        url = f"{ICON_BASE_URL}/{hour_str}/{var_dir}/icon_global_icosahedral_{pressure_level:03d}level_{date_str}{hour_str}_{forecast_hour:03d}_{var_icon}.grib2.bz2"
    else:
        # Single level: icon_global_icosahedral_single-level_2026091000_000_T_2M.grib2.bz2
        url = f"{ICON_BASE_URL}/{hour_str}/{var_dir}/icon_global_icosahedral_single-level_{date_str}{hour_str}_{forecast_hour:03d}_{var_icon}.grib2.bz2"
    
    return url


def download_icon_variable(variable_type, var_internal, var_dir, var_icon, init_time, forecast_hours, output_dir, pressure_level=None):
    var_display = f"{var_internal}" + (f" @ {pressure_level}hPa" if pressure_level else "")
    print(f"[ICON-DOWNLOAD] Baixando {var_display}...")
    
    success_count = 0
    
    for hour in forecast_hours:
        url = get_icon_url(variable_type, var_dir, var_icon, init_time, hour, pressure_level)
        
        safe_var = var_internal.replace("/", "_")
        if pressure_level:
            output_file = output_dir / f"{safe_var}_{pressure_level}hpa_{init_time.strftime('%Y%m%d_%H')}_{hour:03d}.grib2"
        else:
            output_file = output_dir / f"{safe_var}_{init_time.strftime('%Y%m%d_%H')}_{hour:03d}.grib2"
        
        try:
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            
            content = response.content
            
            # Se for bz2, descomprimir
            if url.endswith('.bz2'):
                import bz2
                content = bz2.decompress(content)
            
            with open(output_file, 'wb') as f:
                f.write(content)
            
            file_size = len(content) / 1024 / 1024  # MB
            print(f"[ICON-DOWNLOAD] ✓ {var_internal} F{hour:03d} ({file_size:.2f} MB)")
            success_count += 1
            
        except requests.exceptions.RequestException as e:
            print(f"[ICON-DOWNLOAD] ⚠ {var_internal} F{hour:03d}: {str(e)[:50]}")
        except Exception as e:
            print(f"[ICON-DOWNLOAD] ✗ Erro: {e}")
    
    return success_count > 0


def main():
    parser = argparse.ArgumentParser(description="Download ICON data for CIM WRF 3 KM")
    parser.add_argument("--init-time", required=True, help="Initial time")
    parser.add_argument("--hours", default="0,3,6", help="Forecast hours")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--test-mode", action="store_true", help="Test mode")
    parser.add_argument("--dry-run", action="store_true", help="Show URLs only")
    
    args = parser.parse_args()
    
    try:
        init_time = parse_init_time(args.init_time)
        print(f"[ICON-DOWNLOAD] Init time: {init_time}")
    except ValueError as e:
        print(f"[ICON-DOWNLOAD] Erro: {e}")
        sys.exit(1)
    
    forecast_hours = generate_forecast_hours(args.hours)
    print(f"[ICON-DOWNLOAD] Forecast hours: {forecast_hours}")
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"[ICON-DOWNLOAD] Output directory: {output_dir}")
    
    if args.test_mode:
        print("[ICON-DOWNLOAD] TEST MODE: Downloading minimal dataset...")
        test_single_vars = [("t_2m", "t_2m", "T_2M")]
        test_pressure_vars = []
        test_hours = [0]
    elif args.dry_run:
        test_single_vars = ICON_VARIABLES["single-level"][:3]
        test_pressure_vars = []
        test_hours = [0, 3, 6]
    else:
        test_single_vars = ICON_VARIABLES["single-level"][:5]
        test_pressure_vars = ICON_VARIABLES["pressure-level"][:2]
        test_hours = forecast_hours[:3]
    
    success_count = 0
    total_count = 0
    
    for var_internal, var_dir, var_icon in test_single_vars:
        total_count += 1
        if download_icon_variable("single-level", var_internal, var_dir, var_icon, init_time, test_hours, output_dir):
            success_count += 1
    
    for var_internal, var_dir, var_icon in test_pressure_vars:
        for level in PRESSURE_LEVELS[:5]:
            total_count += 1
            if download_icon_variable("pressure-level", var_internal, var_dir, var_icon, init_time, test_hours, output_dir, level):
                success_count += 1
    
    if args.dry_run:
        print("\n[ICON-DOWNLOAD] DRY RUN complete")
        sys.exit(0)
    
    print(f"\n[ICON-DOWNLOAD] Resumo: {success_count}/{total_count} variáveis baixadas")
    
    if success_count == 0:
        print("[ICON-DOWNLOAD] FALHA: Nenhuma variável baixada")
        sys.exit(1)
    
    print("[ICON-DOWNLOAD] SUCESSO")
    sys.exit(0)


if __name__ == "__main__":
    main()
