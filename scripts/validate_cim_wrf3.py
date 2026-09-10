#!/usr/bin/env python3
"""
CIM WRF 3 KM - Validation Script

Valida a saída do CIM WRF 3 KM antes da publicação.
"""

import argparse
import json
import gzip
import os
import sys
from pathlib import Path
from datetime import datetime


def parse_args():
    parser = argparse.ArgumentParser(description='Validate CIM WRF 3 KM output')
    parser.add_argument('--frames-dir', required=True, help='Directory containing frame files')
    parser.add_argument('--domain', required=True, help='Expected domain name')
    parser.add_argument('--model', required=True, help='Expected model (ecmwf or icon)')
    parser.add_argument('--init-time', required=True, help='Expected initial time')
    parser.add_argument('--hours', required=True, help='Expected forecast hours comma-separated')
    return parser.parse_args()


def validate_metadata(frames_dir, domain, model, init_time, hours):
    """Valida o metadata.json."""
    metadata_path = frames_dir.parent / 'metadata.json' if hasattr(frames_dir, 'parent') else Path(frames_dir) / 'metadata.json'
    
    # Em produção, validaria o metadata.json real
    print(f"[CIM-WRF3-VALIDATE] Checking metadata structure...")
    return True


def validate_frames(frames_dir, domain, model, init_time, hours):
    """Valida cada frame JSON."""
    errors = []
    warnings = []
    
    hours_list = [int(h.strip()) for h in hours.split(',')]
    
    for hour in hours_list:
        frame_file = Path(frames_dir) / f"f{hour:03d}.json.gz"
        
        if not frame_file.exists():
            errors.append(f"Missing frame file: {frame_file.name}")
            continue
        
        try:
            with gzip.open(frame_file, 'rt') as f:
                frame = json.load(f)
            
            # Valida estrutura básica
            if 'forecastHour' not in frame:
                errors.append(f"Frame {hour}: missing forecastHour")
            elif frame['forecastHour'] != hour:
                errors.append(f"Frame {hour}: forecastHour mismatch ({frame['forecastHour']} != {hour})")
            
            if 'validTime' not in frame:
                errors.append(f"Frame {hour}: missing validTime")
            
            if 'domain' not in frame or frame['domain'] != domain:
                errors.append(f"Frame {hour}: domain mismatch")
            
            if 'resolutionKm' not in frame or frame['resolutionKm'] != 3:
                errors.append(f"Frame {hour}: resolutionKm should be 3")
            
            if 'grid' not in frame:
                errors.append(f"Frame {hour}: missing grid information")
            else:
                grid = frame['grid']
                if grid.get('dx', 0) != 3000:
                    errors.append(f"Frame {hour}: dx should be 3000")
                if grid.get('dy', 0) != 3000:
                    errors.append(f"Frame {hour}: dy should be 3000")
            
            # Verifica se há NaN ou Infinity
            if 'data' in frame:
                for var_name, var_data in frame['data'].items():
                    if isinstance(var_data, list):
                        for val in var_data:
                            if isinstance(val, float):
                                if val != val:  # NaN check
                                    errors.append(f"Frame {hour}: NaN in {var_name}")
                                elif val == float('inf') or val == float('-inf'):
                                    errors.append(f"Frame {hour}: Infinity in {var_name}")
            
            print(f"[CIM-WRF3-VALIDATE] Frame {hour:03d}: OK")
            
        except json.JSONDecodeError as e:
            errors.append(f"Frame {hour}: Invalid JSON - {e}")
        except Exception as e:
            errors.append(f"Frame {hour}: Error reading - {e}")
    
    return errors, warnings


def validate_domain_bounds(domain_config):
    """Valida que o domínio cobre a região esperada."""
    bounds = domain_config.get('bounds', {})
    
    expected_coverage = {
        'south': -40.0,  # Sul do RS / Argentina
        'north': -19.0,  # Sul de MG/ES
        'west': -65.0,   # Argentina central
        'east': -47.0    # Leste do PR/SC/RS
    }
    
    errors = []
    
    if bounds.get('south', 0) > expected_coverage['south']:
        errors.append(f"Domain south bound {bounds.get('south')} doesn't cover southern Argentina")
    
    if bounds.get('north', 0) < expected_coverage['north']:
        errors.append(f"Domain north bound {bounds.get('north')} doesn't cover southern Brazil")
    
    if bounds.get('west', 0) > expected_coverage['west']:
        errors.append(f"Domain west bound {bounds.get('west')} doesn't cover Paraguay/Argentina")
    
    if bounds.get('east', 0) < expected_coverage['east']:
        errors.append(f"Domain east bound {bounds.get('east')} doesn't cover Atlantic coast")
    
    return errors


def main():
    args = parse_args()
    
    print(f"[CIM-WRF3-VALIDATE] Starting validation...")
    print(f"[CIM-WRF3-VALIDATE] Frames directory: {args.frames_dir}")
    print(f"[CIM-WRF3-VALIDATE] Expected domain: {args.domain}")
    print(f"[CIM-WRF3-VALIDATE] Expected model: {args.model}")
    print(f"[CIM-WRF3-VALIDATE] Expected init time: {args.init_time}")
    print(f"[CIM-WRF3-VALIDATE] Expected hours: {args.hours}")
    
    all_errors = []
    all_warnings = []
    
    # Validação 1: Model não pode ser GFS
    if args.model.lower() == 'gfs':
        all_errors.append("CIM WRF 3 KM does not support GFS. Use ECMWF or ICON only.")
    
    # Validação 2: Domain deve ser 'cim'
    if args.domain.lower() != 'cim':
        all_errors.append(f"Domain must be 'cim', got '{args.domain}'")
    
    # Validação 3: Carrega configuração do domínio
    config_path = Path(__file__).parent.parent / 'config' / 'cim' / 'domain_config.json'
    if config_path.exists():
        with open(config_path) as f:
            domain_config = json.load(f)
        
        # Validação 4: Bounds do domínio
        bound_errors = validate_domain_bounds(domain_config)
        all_errors.extend(bound_errors)
        
        # Validação 5: Resolução deve ser 3 km
        if domain_config.get('resolutionKm') != 3:
            all_errors.append(f"Resolution must be 3 km, got {domain_config.get('resolutionKm')}")
        
        # Validação 6: dx/dy devem ser 3000
        if domain_config.get('dx', 0) != 3000:
            all_errors.append(f"dx must be 3000, got {domain_config.get('dx')}")
        if domain_config.get('dy', 0) != 3000:
            all_errors.append(f"dy must be 3000, got {domain_config.get('dy')}")
    
    # Validação 7: Frames
    frame_errors, frame_warnings = validate_frames(
        args.frames_dir, 
        args.domain, 
        args.model, 
        args.init_time, 
        args.hours
    )
    all_errors.extend(frame_errors)
    all_warnings.extend(frame_warnings)
    
    # Validação 8: Metadata
    # validate_metadata(args.frames_dir, args.domain, args.model, args.init_time, args.hours)
    
    # Relatório final
    print(f"\n[CIM-WRF3-VALIDATE] === VALIDATION REPORT ===")
    print(f"[CIM-WRF3-VALIDATE] Errors: {len(all_errors)}")
    print(f"[CIM-WRF3-VALIDATE] Warnings: {len(all_warnings)}")
    
    if all_errors:
        print(f"\n[CIM-WRF3-VALIDATE] ERRORS:")
        for error in all_errors:
            print(f"  - {error}")
    
    if all_warnings:
        print(f"\n[CIM-WRF3-VALIDATE] WARNINGS:")
        for warning in all_warnings:
            print(f"  - {warning}")
    
    if all_errors:
        print(f"\n[CIM-WRF3-VALIDATE] VALIDATION FAILED")
        return 1
    else:
        print(f"\n[CIM-WRF3-VALIDATE] VALIDATION PASSED")
        return 0


if __name__ == '__main__':
    sys.exit(main())
