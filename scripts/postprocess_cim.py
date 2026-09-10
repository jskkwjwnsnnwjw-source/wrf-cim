#!/usr/bin/env python3
"""
Pós-processamento de saída WRF para CIM WRF 3 KM
Converte wrfout_d01 em frames JSON para o frontend

Uso:
    python3 postprocess_cim.py --input ./wrfout --output ./frames --domain cim --model ecmwf
"""

import argparse
import os
import sys
import json
import gzip
import numpy as np
from datetime import datetime, timedelta

try:
    from netCDF4 import Dataset
except ImportError:
    print("ERRO: netCDF4 não instalado. Execute: pip install netCDF4")
    sys.exit(1)

def parse_args():
    parser = argparse.ArgumentParser(description='Post-process WRF output for CIM')
    parser.add_argument('--input', required=True, help='Input wrfout file or directory')
    parser.add_argument('--output', required=True, help='Output directory for frames')
    parser.add_argument('--domain', default='cim', help='Domain name')
    parser.add_argument('--model', required=True, choices=['ecmwf', 'icon'], help='Initial model source')
    parser.add_argument('--init-time', required=True, help='Initialization time (ISO format)')
    parser.add_argument('--hours', default='0,3,6,9,12,15,18,21,24,27,30,33,36', help='Forecast hours to process')
    return parser.parse_args()

def extract_variable(nc, var_name, time_idx=0):
    """Extrair variável do NetCDF como array numpy"""
    try:
        var = nc.variables[var_name]
        if len(var.shape) == 4:  # (Time, Level, Lat, Lon) ou (Time, Level, Lat, Lon)
            data = var[time_idx, :, :, :]
        elif len(var.shape) == 3:  # (Time, Lat, Lon)
            data = var[time_idx, :, :]
        else:
            data = var[time_idx]
        return data[:]
    except KeyError:
        return None
    except Exception as e:
        print(f"[CIM-POST] Warning: Could not extract {var_name}: {e}")
        return None

def create_frame(init_time, forecast_hour, lat, lon, data_vars):
    """Criar estrutura de frame para o frontend"""
    valid_time = init_time + timedelta(hours=forecast_hour)
    
    frame = {
        'forecastHour': forecast_hour,
        'validTime': valid_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'initTime': init_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'grid': {
            'lat': lat.flatten().tolist(),
            'lon': lon.flatten().tolist(),
            'shape': list(lat.shape)
        },
        'fields': {}
    }
    
    # Adicionar campos disponíveis
    for var_name, var_data in data_vars.items():
        if var_data is not None:
            # Reduzir precisão para economizar espaço
            if var_data.dtype == np.float64:
                var_data = var_data.astype(np.float32)
            
            # Mask NaN/Infinity
            var_data = np.nan_to_num(var_data, nan=-9999.0, posinf=99999.0, neginf=-99999.0)
            
            frame['fields'][var_name] = var_data.tolist()
    
    return frame

def save_frame_gzip(frame, output_path):
    """Salvar frame como JSON.GZ"""
    json_str = json.dumps(frame, separators=(',', ':'))
    with gzip.open(output_path, 'wt', encoding='utf-8', compresslevel=9) as f:
        f.write(json_str)

def main():
    args = parse_args()
    
    # Parse horas
    forecast_hours = [int(h.strip()) for h in args.hours.split(',')]
    init_time = datetime.fromisoformat(args.init_time.replace('Z', '+00:00'))
    
    # Criar diretório de saída
    os.makedirs(args.output, exist_ok=True)
    
    print(f"[CIM-WRF3-POST] Input: {args.input}")
    print(f"[CIM-WRF3-POST] Output: {args.output}")
    print(f"[CIM-WRF3-POST] Domain: {args.domain}")
    print(f"[CIM-WRF3-POST] Model: {args.model}")
    print(f"[CIM-WRF3-POST] Init time: {args.init_time}")
    print(f"[CIM-WRF3-POST] Forecast hours: {forecast_hours}")
    print()
    
    # Encontrar arquivo wrfout
    wrf_file = None
    if os.path.isfile(args.input):
        wrf_file = args.input
    elif os.path.isdir(args.input):
        for f in os.listdir(args.input):
            if f.startswith('wrfout_d01'):
                wrf_file = os.path.join(args.input, f)
                break
    
    if not wrf_file or not os.path.exists(wrf_file):
        print(f"[CIM-WRF3-POST] ERRO: wrfout file not found")
        sys.exit(1)
    
    print(f"[CIM-WRF3-POST] Processing: {wrf_file}")
    
    # Abrir arquivo NetCDF
    try:
        nc = Dataset(wrf_file, 'r')
    except Exception as e:
        print(f"[CIM-WRF3-POST] ERRO: Cannot open NetCDF: {e}")
        sys.exit(1)
    
    # Extrair coordenadas
    try:
        XLAT = nc.variables['XLAT'][0, :, :]
        XLONG = nc.variables['XLONG'][0, :, :]
        times = nc.variables['Times'][:].astype(str)
    except Exception as e:
        print(f"[CIM-WRF3-POST] ERRO: Cannot read coordinates: {e}")
        nc.close()
        sys.exit(1)
    
    print(f"[CIM-WRF3-POST] Grid shape: {XLAT.shape}")
    print(f"[CIM-WRF3-POST] Available times: {len(times)}")
    
    # Mapear índice do tempo para hora de previsão
    # Normalmente cada time step é 1 hora no wrfout padrão
    processed_frames = []
    
    for hour in forecast_hours:
        # Estimar índice do tempo (assume 1 hora por time step)
        time_idx = min(hour, len(times) - 1)
        
        print(f"[CIM-WRF3-POST] Processing F{hour:03d} (time_idx={time_idx})...")
        
        # Extrair variáveis principais
        data_vars = {}
        
        # Temperatura 2m
        t2m = extract_variable(nc, 'T2', time_idx)
        if t2m is not None:
            data_vars['temperature_2m'] = t2m - 273.15  # Converter para Celsius
        
        # Umidade 2m
        rh2m = extract_variable(nc, 'RH2', time_idx)
        if rh2m is not None:
            data_vars['humidity_2m'] = rh2m
        
        # Vento 10m
        u10 = extract_variable(nc, 'U10', time_idx)
        v10 = extract_variable(nc, 'V10', time_idx)
        if u10 is not None and v10 is not None:
            data_vars['wind_u_10m'] = u10
            data_vars['wind_v_10m'] = v10
        
        # Precipitação acumulada
        rain = extract_variable(nc, 'RAINNC', time_idx)
        rainc = extract_variable(nc, 'RAINC', time_idx)
        if rain is not None:
            if rainc is not None:
                data_vars['precipitation'] = rain + rainc
            else:
                data_vars['precipitation'] = rain
        
        # Refletividade (se disponível)
        refl = extract_variable(nc, 'REFL_10CM', time_idx)
        if refl is not None:
            data_vars['reflectivity'] = refl
            data_vars['reflectivitySource'] = 'REFL_10CM_NATIVE'
        
        # CAPE (se disponível)
        cape = extract_variable(nc, 'MUCAPE', time_idx)
        if cape is not None:
            data_vars['mucape'] = cape
        
        # Criar frame
        frame = create_frame(init_time, hour, XLAT, XLONG, data_vars)
        
        # Salvar frame
        filename = f"f{hour:03d}.json.gz"
        output_path = os.path.join(args.output, filename)
        save_frame_gzip(frame, output_path)
        
        file_size = os.path.getsize(output_path) / 1024  # KB
        print(f"[CIM-WRF3-POST] Generated {filename} ({file_size:.1f} KB)")
        processed_frames.append({
            'forecastHour': hour,
            'validTime': frame['validTime'],
            'file': filename
        })
    
    nc.close()
    
    # Gerar metadata.json
    metadata = {
        'product': 'CIM WRF 3 KM',
        'domain': args.domain,
        'resolutionKm': 3,
        'model': args.model,
        'initTime': args.init_time,
        'runCycle': init_time.strftime('%H') + 'z',
        'status': 'complete',
        'reflectivitySource': 'REFL_10CM_NATIVE' if 'reflectivity' in data_vars else 'UNAVAILABLE',
        'frameCount': len(processed_frames),
        'frames': processed_frames,
        'generatedAt': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    }
    
    metadata_path = os.path.join(args.output, 'metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print()
    print("=" * 50)
    print(f"[CIM-WRF3-POST] Generated {len(processed_frames)} frames")
    print(f"[CIM-WRF3-POST] Metadata: {metadata_path}")
    print("[CIM-WRF3-POST] Post-processing completed successfully")

if __name__ == '__main__':
    main()
