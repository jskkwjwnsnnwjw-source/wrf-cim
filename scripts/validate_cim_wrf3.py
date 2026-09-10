#!/usr/bin/env python3
"""
Validação de dados CIM WRF 3 KM antes da publicação
Verifica integridade dos frames e metadata

Uso:
    python3 validate_cim_wrf3.py --frames-dir ./frames --domain cim --model ecmwf
"""

import argparse
import os
import sys
import json
import gzip

def parse_args():
    parser = argparse.ArgumentParser(description='Validate CIM WRF 3 KM data')
    parser.add_argument('--frames-dir', required=True, help='Directory containing frames')
    parser.add_argument('--domain', default='cim', help='Expected domain name')
    parser.add_argument('--model', required=True, choices=['ecmwf', 'icon'], help='Expected model source')
    parser.add_argument('--init-time', help='Expected init time (ISO format)')
    parser.add_argument('--hours', help='Expected forecast hours comma-separated')
    return parser.parse_args()

def validate_metadata(metadata_path, expected_domain, expected_model, expected_init_time):
    """Validar arquivo metadata.json"""
    if not os.path.exists(metadata_path):
        return False, "metadata.json not found"
    
    try:
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
    except Exception as e:
        return False, f"Cannot read metadata.json: {e}"
    
    # Verificar campos obrigatórios
    required_fields = ['product', 'domain', 'resolutionKm', 'model', 'initTime', 'status', 'frames']
    for field in required_fields:
        if field not in metadata:
            return False, f"Missing required field: {field}"
    
    # Validar valores
    if metadata['domain'] != expected_domain:
        return False, f"Domain mismatch: expected {expected_domain}, got {metadata['domain']}"
    
    if metadata['model'] != expected_model:
        return False, f"Model mismatch: expected {expected_model}, got {metadata['model']}"
    
    if metadata['resolutionKm'] != 3:
        return False, f"Resolution mismatch: expected 3 km, got {metadata['resolutionKm']}"
    
    if metadata['status'] != 'complete':
        return False, f"Status is not complete: {metadata['status']}"
    
    if not isinstance(metadata['frames'], list) or len(metadata['frames']) == 0:
        return False, "Frames array is empty or invalid"
    
    # Verificar init time se fornecido
    if expected_init_time and metadata['initTime'] != expected_init_time:
        return False, f"Init time mismatch: expected {expected_init_time}, got {metadata['initTime']}"
    
    return True, "OK"

def validate_frame(frame_path, expected_domain, expected_model):
    """Validar um frame individual"""
    if not os.path.exists(frame_path):
        return False, "File not found"
    
    try:
        with gzip.open(frame_path, 'rt', encoding='utf-8') as f:
            frame = json.load(f)
    except Exception as e:
        return False, f"Cannot read frame: {e}"
    
    # Verificar campos obrigatórios
    required_fields = ['forecastHour', 'validTime', 'initTime', 'grid', 'fields']
    for field in required_fields:
        if field not in frame:
            return False, f"Missing field: {field}"
    
    # Validar grid
    if 'lat' not in frame['grid'] or 'lon' not in frame['grid']:
        return False, "Grid missing lat/lon"
    
    if len(frame['grid']['lat']) != len(frame['grid']['lon']):
        return False, "Grid lat/lon size mismatch"
    
    # Verificar se há campos válidos
    if not frame['fields']:
        return False, "No fields in frame"
    
    # Verificar NaN/Infinity nos campos
    for field_name, field_data in frame['fields'].items():
        if isinstance(field_data, list):
            # Verificar alguns valores amostrais
            sample = field_data[:10] if len(field_data) > 10 else field_data
            for val in sample:
                if val is None or (isinstance(val, float) and (val != val)):  # NaN check
                    return False, f"Invalid value in field {field_name}"
    
    return True, "OK"

def main():
    args = parse_args()
    
    print(f"[CIM-WRF3-VALIDATE] Frames directory: {args.frames_dir}")
    print(f"[CIM-WRF3-VALIDATE] Expected domain: {args.domain}")
    print(f"[CIM-WRF3-VALIDATE] Expected model: {args.model}")
    print()
    
    errors = []
    
    # Validar metadata
    metadata_path = os.path.join(args.frames_dir, 'metadata.json')
    valid, msg = validate_metadata(metadata_path, args.domain, args.model, args.init_time)
    if not valid:
        errors.append(f"Metadata validation failed: {msg}")
        print(f"[CIM-WRF3-VALIDATE] Metadata: FAIL - {msg}")
    else:
        print(f"[CIM-WRF3-VALIDATE] Metadata: OK")
    
    # Carregar metadata para validar frames
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            expected_hours = [frame['forecastHour'] for frame in metadata.get('frames', [])]
        except:
            expected_hours = []
            errors.append("Could not read frames from metadata")
    else:
        expected_hours = []
    
    # Validar cada frame
    if expected_hours:
        for hour in expected_hours:
            frame_filename = f"f{hour:03d}.json.gz"
            frame_path = os.path.join(args.frames_dir, frame_filename)
            
            valid, msg = validate_frame(frame_path, args.domain, args.model)
            if valid:
                print(f"[CIM-WRF3-VALIDATE] Frame {hour:03d}: OK")
            else:
                errors.append(f"Frame {hour:03d} validation failed: {msg}")
                print(f"[CIM-WRF3-VALIDATE] Frame {hour:03d}: FAIL - {msg}")
    
    print()
    print("=" * 50)
    
    if errors:
        print(f"[CIM-WRF3-VALIDATE] VALIDATION FAILED")
        print(f"Errors: {len(errors)}")
        for err in errors[:5]:  # Mostrar apenas primeiros 5 erros
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("[CIM-WRF3-VALIDATE] VALIDATION PASSED")
        sys.exit(0)

if __name__ == '__main__':
    main()
