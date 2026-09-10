#!/bin/bash
# Script para executar CIM WRF 3 KM diariamente
# Inicia em 13/08/2026 e continua automaticamente

set -e

echo "=============================================="
echo "CIM WRF 3 KM — Processamento Diário Automático"
echo "=============================================="

# Configurações
START_DATE="2026-08-13"
INIT_HOURS="06 12 18"  # 06z, 12z, 18z
FORECAST_HOURS="0,3,6,9,12,15,18,21,24,27,30,33,36"
TEST_MODE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --start-date) START_DATE="$2"; shift 2 ;;
        --hours) INIT_HOURS="$2"; shift 2 ;;
        --test-mode) TEST_MODE=true; shift ;;
        --help)
            echo "Uso: $0 [--start-date YYYY-MM-DD] [--hours 'HH HH HH'] [--test-mode]"
            echo "  --start-date  Data inicial (padrão: 2026-08-13)"
            echo "  --hours       Horários de inicialização (padrão: 06 12 18)"
            echo "  --test-mode   Modo de teste (baixa apenas F000-F006)"
            exit 0
            ;;
        *) echo "Opção desconhecida: $1"; exit 1 ;;
    esac
done

echo "Data inicial: $START_DATE"
echo "Horários: $INIT_HOURS"
echo "Modo teste: $TEST_MODE"
echo ""

# Função para processar uma rodada
process_run() {
    local date=$1
    local hour=$2
    local init_time="${date}T${hour}:00:00Z"
    
    echo ""
    echo "=========================================="
    echo "Processando: $init_time"
    echo "=========================================="
    
    # ECMWF
    echo "[ECMWF] Baixando dados..."
    if [ "$TEST_MODE" = true ]; then
        python3 scripts/download_ecmwf.py \
            -i "$init_time" \
            -f "0,3,6" \
            -o "./ecmwf_${date}_${hour}" \
            -t
    else
        python3 scripts/download_ecmwf.py \
            -i "$init_time" \
            -f "$FORECAST_HOURS" \
            -o "./ecmwf_${date}_${hour}"
    fi
    
    # ICON
    echo "[ICON] Baixando dados..."
    if [ "$TEST_MODE" = true ]; then
        python3 scripts/download_icon.py \
            --init-time "$init_time" \
            --hours "0,3,6" \
            --output-dir "./icon_${date}_${hour}" \
            --test-mode
    else
        python3 scripts/download_icon.py \
            --init-time "$init_time" \
            --hours "$FORECAST_HOURS" \
            --output-dir "./icon_${date}_${hour}"
    fi
    
    echo "✓ Rodada $init_time concluída"
}

# Loop principal - processa todos os dias a partir da data inicial
CURRENT_DATE="$START_DATE"
TODAY=$(date +%Y-%m-%d)

echo ""
echo "Iniciando processamento automático..."
echo "Data atual do sistema: $TODAY"
echo ""

while [[ "$CURRENT_DATE" < "$TODAY" ]] || [[ "$CURRENT_DATE" == "$TODAY" ]]; do
    echo ""
    echo "########################################"
    echo "# Dia: $CURRENT_DATE"
    echo "########################################"
    
    for hour in $INIT_HOURS; do
        # Formatar hora com zero à esquerda
        hour_fmt=$(printf "%02d" $hour)
        
        # Verificar se já não foi processado
        if [ -d "ecmwf_${CURRENT_DATE}_${hour_fmt}" ] && [ -d "icon_${CURRENT_DATE}_${hour_fmt}" ]; then
            echo "[SKIP] Rodada ${hour_fmt}z já processada"
            continue
        fi
        
        process_run "$CURRENT_DATE" "$hour_fmt"
    done
    
    # Avançar para próximo dia
    CURRENT_DATE=$(date -d "$CURRENT_DATE + 1 day" +%Y-%m-%d)
done

echo ""
echo "=============================================="
echo "✓ Processamento automático concluído!"
echo "=============================================="
