#!/usr/bin/env python3
"""
Download de dados ECMWF para o CIM WRF 3 KM

Este script baixa os campos necessários do ECMWF via CDS API
para inicializar o modelo regional CIM WRF 3 KM.

Uso:
    python3 download_ecmwf.py --init-time 2024-01-15T12:00:00Z --hours 0,3,6,9,12 --output-dir /tmp/ecmwf_data

Requisitos:
    - pip install cdsapi
    - Chave de API CDS configurada em ~/.cdsapirc
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    import cdsapi
except ImportError:
    print("[ECMWF-DOWNLOAD] Instalando cdsapi...")
    os.system("pip3 install cdsapi")
    import cdsapi


# Domínio CIM WRF 3 KM - Cone Sul
# Precisamos baixar uma área maior que o domínio para evitar problemas de borda
CIM_BOUNDS = {
    "north": -15.0,   # Um pouco mais ao norte para margem
    "south": -45.0,   # Um pouco mais ao sul para margem
    "west": -70.0,    # Um pouco mais a oeste para margem
    "east": -42.0     # Um pouco mais a leste para margem
}

# Variáveis necessárias para o WRF (via WPS/ungrib)
# Lista baseada nas tabelas Vtable do WPS
ECMWF_VARIABLES = [
    # Nível de superfície
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
    "2m_temperature",
    "2m_dewpoint_temperature",
    "mean_sea_level_pressure",
    "surface_pressure",
    "skin_temperature",
    "soil_temperature_level_1",
    "soil_temperature_level_2",
    "soil_temperature_level_3",
    "soil_temperature_level_4",
    "volumetric_soil_water_layer_1",
    "volumetric_soil_water_layer_2",
    "volumetric_soil_water_layer_3",
    "volumetric_soil_water_layer_4",
    
    # Níveis de pressão (para perfis verticais)
    # Estes são baixados em múltiplos níveis
]

# Níveis de pressão padrão para inicialização WRF
PRESSURE_LEVELS = [
    1000, 975, 950, 925, 900, 850, 800, 750, 700, 650,
    600, 550, 500, 450, 400, 350, 300, 250, 225, 200,
    175, 150, 125, 100, 75, 50, 30, 20, 10
]

# Variáveis em níveis de pressão
PRESSURE_LEVEL_VARIABLES = [
    "geopotential",
    "temperature",
    "u_component_of_wind",
    "v_component_of_wind",
    "relative_humidity",
    "specific_humidity"
]


def parse_init_time(init_time_str):
    """Parse init time string para datetime"""
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
    raise ValueError(f"Formato de tempo não reconhecido: {init_time_str}")


def generate_forecast_hours(hours_str):
    """Gera lista de horas de forecast a partir de string comma-separated"""
    if not hours_str:
        return list(range(0, 37, 3))  # Default: 0-36h de 3 em 3 horas
    return [int(h.strip()) for h in hours_str.split(",")]


def download_ecmwf_variable(cds, variable, init_time, forecast_hours, output_dir, bounds):
    """Baixa uma variável específica do ECMWF"""
    print(f"[ECMWF-DOWNLOAD] Baixando {variable}...")
    
    # Formatar horas de forecast
    step_hours = sorted(set(forecast_hours))
    step_strings = [f"{h:03d}" for h in step_hours]
    
    # Formato de data para CDS
    date_str = init_time.strftime("%Y-%m-%d")
    time_str = init_time.strftime("%H:00")
    
    # Nome do arquivo de saída
    safe_var = variable.replace("/", "_")
    output_file = output_dir / f"{safe_var}_{date_str}_{time_str}.grib"
    
    # Preparar request baseado no tipo de variável
    if variable in PRESSURE_LEVEL_VARIABLES:
        # Variáveis em múltiplos níveis de pressão
        request = {
            "product_type": "forecast",
            "format": "grib",
            "variable": variable,
            "pressure_level": [str(p) for p in PRESSURE_LEVELS],
            "date": date_str,
            "time": time_str,
            "step": step_strings,
            "area": [bounds["north"], bounds["west"], bounds["south"], bounds["east"]],
        }
    else:
        # Variáveis de superfície única
        request = {
            "product_type": "forecast",
            "format": "grib",
            "variable": variable,
            "date": date_str,
            "time": time_str,
            "step": step_strings,
            "area": [bounds["north"], bounds["west"], bounds["south"], bounds["east"]],
        }
    
    try:
        cds.retrieve("reanalysis-era5-single-levels" if variable not in PRESSURE_LEVEL_VARIABLES 
                     else "reanalysis-era5-pressure-levels", request, str(output_file))
        print(f"[ECMWF-DOWNLOAD] ✓ {variable} salvo em {output_file}")
        return True
    except Exception as e:
        print(f"[ECMWF-DOWNLOAD] ✗ Erro ao baixar {variable}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Download ECMWF data for CIM WRF 3 KM")
    parser.add_argument("--init-time", required=True, help="Initial time (YYYY-MM-DDTHH:MM:SSZ)")
    parser.add_argument("--hours", default="0,3,6", help="Forecast hours (comma-separated)")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--test-mode", action="store_true", help="Test mode with minimal data")
    
    args = parser.parse_args()
    
    # Parse init time
    try:
        init_time = parse_init_time(args.init_time)
        print(f"[ECMWF-DOWNLOAD] Init time: {init_time}")
    except ValueError as e:
        print(f"[ECMWF-DOWNLOAD] Erro: {e}")
        sys.exit(1)
    
    # Generate forecast hours
    forecast_hours = generate_forecast_hours(args.hours)
    print(f"[ECMWF-DOWNLOAD] Forecast hours: {forecast_hours}")
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"[ECMWF-DOWNLOAD] Output directory: {output_dir}")
    
    # Test mode: apenas uma variável e menos horas
    if args.test_mode:
        print("[ECMWF-DOWNLOAD] TEST MODE: Downloading minimal dataset...")
        test_vars = ["2m_temperature"]
        test_hours = [0]
    else:
        test_vars = ECMWF_VARIABLES[:5]  # Primeiras 5 variáveis para teste rápido
        test_hours = forecast_hours[:3]  # Primeiras 3 horas
    
    # Initialize CDS API
    try:
        cds = cdsapi.Client()
        print("[ECMWF-DOWNLOAD] CDS API initialized")
    except Exception as e:
        print(f"[ECMWF-DOWNLOAD] Erro ao inicializar CDS API: {e}")
        print("[ECMWF-DOWNLOAD] Certifique-se de ter ~/.cdsapirc configurado com sua API key")
        print("[ECMWF-DOWNLOAD] Exemplo de ~/.cdsapirc:")
        print("  url: https://cds.climate.copernicus.eu/api/v2")
        print("  key: YOUR_UID:YOUR_API_KEY")
        sys.exit(1)
    
    # Download variables
    success_count = 0
    total_count = len(test_vars)
    
    for var in test_vars:
        if download_ecmwf_variable(cds, var, init_time, test_hours, output_dir, CIM_BOUNDS):
            success_count += 1
    
    print(f"\n[ECMWF-DOWNLOAD] Resumo: {success_count}/{total_count} variáveis baixadas com sucesso")
    
    if success_count == 0:
        print("[ECMWF-DOWNLOAD] FALHA: Nenhuma variável foi baixada")
        sys.exit(1)
    
    print("[ECMWF-DOWNLOAD] SUCESSO: Dados ECMWF prontos para WPS/ungrib")
    sys.exit(0)


if __name__ == "__main__":
    main()
