#!/bin/bash
# Script para criar as branches de dados do CIM WRF 3 KM
# Uso: ./scripts/create_data_branches.sh

set -e

echo "=================================================="
echo "CIM WRF 3 KM - Criando Branches de Dados"
echo "=================================================="

BRANCH_ECMWF="cim-wrf3-ecmwf-data"
BRANCH_ICON="cim-wrf3-icon-data"

# Função para criar branch órfã
create_orphan_branch() {
    local branch_name=$1
    
    if git show-ref --verify --quiet refs/heads/${branch_name}; then
        echo "A branch '${branch_name}' já existe. Pulando."
    else
        echo "Criando branch órfã: ${branch_name}..."
        git checkout --orphan ${branch_name}
        git rm -rf .
        
        # Criar arquivo README na branch de dados
        cat > README.md << EOF
# ${branch_name}

Branch de dados para o modelo CIM WRF 3 KM.

- **Modelo**: WRF 4.4.0
- **Resolução**: 3 km
- **Domínio**: Cone Sul (Sul BR, Paraguai, Uruguai, Argentina)
- **Fonte**: ECMWF ou ICON (dependendo da branch)

Esta branch contém apenas arquivos de dados (metadata.json e frames JSON.GZ).
Não modifique manualmente. Atualizações são feitas automaticamente pelos workflows.
EOF
        
        git add README.md
        git commit -m "Initial commit: CIM WRF 3 KM data branch for ${branch_name}"
        git push origin ${branch_name}
        echo "Branch '${branch_name}' criada e enviada com sucesso."
    fi
}

# Voltar para main antes de começar
git checkout main 2>/dev/null || git checkout master

# Criar branches
create_orphan_branch "${BRANCH_ECMWF}"
create_orphan_branch "${BRANCH_ICON}"

echo ""
echo "=================================================="
echo "SUCESSO!"
echo "Branches criadas:"
echo "  - ${BRANCH_ECMWF}"
echo "  - ${BRANCH_ICON}"
echo "=================================================="
echo ""
echo "Próximos passos:"
echo "1. Atualize os workflows com a URL correta do container Docker"
echo "2. Teste o workflow manualmente no GitHub Actions"
