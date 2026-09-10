#!/usr/bin/env python3
"""
CIM WRF 3 KM - Post-processor

Extrai campos meteorológicos do wrfout e gera frames JSON para o frontend.
"""

import argparse
import json
import gzip
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description='Post-process CIM WRF 3 KM output')
    parser.add_argument('--input', required=True, help='Input directory with wrfout files')
    parser.add_argument('--output', required=True, help='Output directory for frames')
    parser.add_argument('--domain', required=True, help='Domain name (cim)')
    parser.add_argument('--model', required=True, help='Model source (ecmwf or icon)')
    parser.add_argument('--init-time', required=True, help='Initial time ISO format')
    parser.add_argument('--hours', required=True, help='Forecast hours comma-separated')
    return parser.parse_args()


def extract_variables_from_wrf(wrf_file):
    """
    Extrai variáveis meteorológicas de um arquivo wrfout.
    
    Retorna dicionário com:
    - reflectivity: refletividade em dBZ (REFL_10CM se disponível)
    - precipitation: precipitação acumulada
    - cape: MUCAPE
    - u_wind: vento zonal
    - v_wind: vento meridional
    - temperature: temperatura
    - humidity: umidade relativa
    - bulk_shear: Bulk Shear 0-6km
    """
    # Em produção, usaria netCDF4 ou xarray para ler o wrfout
    # Aqui simulamos a estrutura esperada
    
    return {
        'reflectivity': [],
        'precipitation': [],
        'cape': [],
        'u_wind': [],
        'v_wind': [],
        'temperature': [],
        'humidity': [],
        'bulk_shear': []
    }


def generate_frame(forecast_hour, init_time, variables, domain_config):
    """Gera um frame JSON para um determinado forecast hour."""
    
    valid_time = init_time + timedelta(hours=forecast_hour)
    
    frame = {
        'forecastHour': forecast_hour,
        'validTime': valid_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'domain': domain_config['domain'],
        'resolutionKm': domain_config['resolutionKm'],
        'grid': {
            'e_we': domain_config['geogrid']['e_we'],
            'e_sn': domain_config['geogrid']['e_sn'],
            'dx': domain_config['dx'],
            'dy': domain_config['dy']
        },
        'data': {}
    }
    
    # Adiciona dados das variáveis disponíveis
    for var_name, var_data in variables.items():
        if var_data:  # Se houver dados
            frame['data'][var_name] = var_data
    
    return frame


def compress_json(data):
    """Comprime JSON com gzip."""
    json_str = json.dumps(data, separators=(',', ':'))
    return gzip.compress(json_str.encode('utf-8'))


def main():
    args = parse_args()
    
    print(f"[CIM-WRF3-POST] Starting post-processing...")
    print(f"[CIM-WRF3-POST] Input: {args.input}")
    print(f"[CIM-WRF3-POST] Output: {args.output}")
    print(f"[CIM-WRF3-POST] Domain: {args.domain}")
    print(f"[CIM-WRF3-POST] Model: {args.model}")
    print(f"[CIM-WRF3-POST] Init time: {args.init_time}")
    print(f"[CIM-WRF3-POST] Hours: {args.hours}")
    
    # Carrega configuração do domínio
    config_path = Path(__file__).parent.parent / 'config' / 'cim' / 'domain_config.json'
    with open(config_path) as f:
        domain_config = json.load(f)
    
    # Parse forecast hours
    hours = [int(h.strip()) for h in args.hours.split(',')]
    
    # Parse init time
    init_time = datetime.fromisoformat(args.init_time.replace('Z', '+00:00'))
    
    # Cria diretório de saída
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Processa cada hora de previsão
    for hour in hours:
        print(f"[CIM-WRF3-POST] Processing F{hour:03d}...")
        
        # Encontra arquivo wrfout correspondente
        wrf_filename = f"wrfout_d01_{init_time.strftime('%Y-%m-%d_%H')}:00:00"
        wrf_path = Path(args.input) / wrf_filename
        
        if not wrf_path.exists():
            print(f"[CIM-WRF3-POST] WARNING: wrfout not found: {wrf_path}")
            # Continua mesmo assim para demonstração
        
        # Extrai variáveis (em produção, leria do NetCDF)
        variables = extract_variables_from_wrf(wrf_path)
        
        # Gera frame
        frame = generate_frame(hour, init_time, variables, domain_config)
        
        # Salva frame comprimido
        frame_file = output_dir / f"f{hour:03d}.json.gz"
        compressed_data = compress_json(frame)
        
        with open(frame_file, 'wb') as f:
            f.write(compressed_data)
        
        print(f"[CIM-WRF3-POST] Generated {frame_file.name} ({len(compressed_data)} bytes)")
    
    print(f"[CIM-WRF3-POST] Post-processing completed successfully")
    return 0


if __name__ == '__main__':
    sys.exit(main())
