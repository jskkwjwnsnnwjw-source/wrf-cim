#!/bin/bash
# Script para build e push do container Docker WRF CIM 3KM
# Uso: ./scripts/build_and_push_container.sh

set -e

# Configurações
IMAGE_NAME="wrf-cim-container"
IMAGE_TAG="latest"
GITHUB_REGISTRY="ghcr.io"

# Obter username do GitHub a partir do remote origin
GITHUB_USER=$(git config --get remote.origin.url | sed -n 's/.*github\.com[:/]\([^/]*\).*/\1/p')

if [ -z "$GITHUB_USER" ]; then
    echo "Erro: Não foi possível detectar o usuário do GitHub."
    echo "Configure o remote origin ou defina GITHUB_USER manualmente."
    exit 1
fi

FULL_IMAGE_NAME="${GITHUB_REGISTRY}/${GITHUB_USER,,}/${IMAGE_NAME}"

echo "=================================================="
echo "CIM WRF 3 KM - Build e Push do Container"
echo "=================================================="
echo "Usuário GitHub: ${GITHUB_USER}"
echo "Imagem: ${FULL_IMAGE_NAME}:${IMAGE_TAG}"
echo "=================================================="

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "Erro: Docker não está instalado."
    exit 1
fi

# Fazer login no GitHub Container Registry
echo "Fazendo login no ${GITHUB_REGISTRY}..."
if [ -n "${GHCR_TOKEN}" ]; then
    echo "${GHCR_TOKEN}" | docker login ${GITHUB_REGISTRY} -u "${GITHUB_USER}" --password-stdin
else
    echo "Aviso: GHCR_TOKEN não definido. Tentando login interativo ou usando credenciais existentes."
    echo "Se falhar, execute: echo SEU_TOKEN | docker login ghcr.io -u SEU_USUARIO --password-stdin"
fi

# Build da imagem
echo ""
echo "Iniciando build da imagem Docker (isso pode levar 20-40 minutos)..."
docker build -f Dockerfile.wrf -t ${FULL_IMAGE_NAME}:${IMAGE_TAG} .

# Push da imagem
echo ""
echo "Enviando imagem para ${GITHUB_REGISTRY}..."
docker push ${FULL_IMAGE_NAME}:${IMAGE_TAG}

echo ""
echo "=================================================="
echo "SUCESSO!"
echo "Imagem disponível em: ${FULL_IMAGE_NAME}:${IMAGE_TAG}"
echo "=================================================="
echo ""
echo "Próximos passos:"
echo "1. Atualize os workflows em .github/workflows/ com a URL da imagem"
echo "2. Execute ./scripts/create_data_branches.sh"
echo "3. Teste o workflow manualmente no GitHub Actions"
