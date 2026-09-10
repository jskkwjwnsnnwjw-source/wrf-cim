# 📘 Guia Completo de Setup - CIM WRF 3 KM

Este guia cobre todos os passos necessários para colocar o modelo **CIM WRF 3 KM** em produção usando GitHub Actions.

---

## 📋 Pré-requisitos

1. **Docker instalado** na sua máquina local ou servidor
2. **Acesso de escrita** ao repositório GitHub
3. **GitHub CLI (gh)** instalado (opcional, mas recomendado)
4. **Recursos suficientes**: O build do container requer ~8GB RAM e ~30GB disco

---

## 🚀 Passo a Passo

### Passo 1: Build e Push do Container Docker

O container contém WRF 4.4.0 + WPS 4.4.0 compilados automaticamente.

```bash
# No terminal, na raiz do repositório:
./scripts/build_and_push_container.sh
```

**O que este script faz:**
1. Detecta o owner do repositório automaticamente
2. Faz login no GitHub Container Registry (GHCR)
3. Build da imagem Docker (~15-25 minutos)
4. Push para `ghcr.io/SEU_USUARIO/wrf-cim-container:latest`

**Alternativa manual:**
```bash
docker build -f Dockerfile.wrf -t ghcr.io/SEU_USUARIO/wrf-cim-container:latest .
docker push ghcr.io/SEU_USUARIO/wrf-cim-container:latest
```

---

### Passo 2: Criar Branches de Dados

As branches `cim-wrf3-ecmwf-data` e `cim-wrf3-icon-data` armazenarão os frames JSON.

```bash
./scripts/create_data_branches.sh
```

**O que este script faz:**
1. Cria branch `cim-wrf3-ecmwf-data` (orphan, sem histórico)
2. Cria branch `cim-wrf3-icon-data` (orphan, sem histórico)
3. Push de ambas para o GitHub
4. Retorna para branch `main`

**Alternativa manual:**
```bash
git checkout --orphan cim-wrf3-ecmwf-data
git commit --allow-empty -m "Initial CIM WRF 3 KM ECMWF data branch"
git push origin cim-wrf3-ecmwf-data

git checkout --orphan cim-wrf3-icon-data
git commit --allow-empty -m "Initial CIM WRF 3 KM ICON data branch"
git push origin cim-wrf3-icon-data

git checkout main
```

---

### Passo 3: Configurar Secrets (Opcional)

Para ECMWF Open Data, **não é necessária API key**. Os dados são públicos.

Se quiser usar CDS API no futuro:
1. Vá em **Settings → Secrets and variables → Actions**
2. Adicione `ECMWF_API_KEY` no formato `UID:KEY`

---

### Passo 4: Testar com Workflow Dispatch Manual

1. Vá em **Actions → CIM WRF 3 KM - ECMWF**
2. Clique em **Run workflow**
3. Preencha:
   - **Initial time**: `2026-08-13T06:00:00Z`
   - **Forecast hours**: `0,3,6` (teste curto)
4. Clique em **Run workflow**

**Tempo estimado**: 45-90 minutos para 6 horas de previsão

**Verificação após conclusão:**
```bash
git fetch origin cim-wrf3-ecmwf-data
git checkout cim-wrf3-ecmwf-data
ls -la
# Deve mostrar: metadata.json, f000.json.gz, f003.json.gz, f006.json.gz
```

---

### Passo 5: Agendamento Automático

Os workflows já estão configurados para rodar automaticamente:

| Horário UTC | Cron | Rodada ECMWF/ICON |
|-------------|------|-------------------|
| 06z | `15 06 * * *` | 06:00 UTC |
| 08z | `15 08 * * *` | 08:00 UTC |
| 12z | `15 12 * * *` | 12:00 UTC |
| 18z | `15 18 * * *` | 18:00 UTC |
| 21z | `15 21 * * *` | 21:00 UTC |

O workflow inicia 15 minutos após a hora cheia para dar tempo dos dados ficarem disponíveis.

---

## 🔧 Integração Frontend

Edite `refletividaded.html` conforme descrito em `FRONTEND_INTEGRATION.md`:

### 1. Adicionar opções no select
```html
<optgroup label="CIM WRF 3 KM — Sul / Paraguai / Uruguai / Argentina">
    <option value="ecmwf_cim_wrf3">ECMWF → CIM WRF 3 KM</option>
    <option value="icon_cim_wrf3">ICON → CIM WRF 3 KM</option>
</optgroup>
```

### 2. Adicionar domínio CIM
```javascript
const MODEL_DOMAIN_BOUNDS = {
    // ... existentes ...
    'cim': {
        bounds: [[-40.0, -65.0], [-19.0, -47.0]],
        label: 'CIM · Sul / PY / UY / AR',
        center: [-29.5, -56.0],
        zoom: 6
    }
};
```

### 3. Mapear modelos para domínio
```javascript
function domainKeyForModel(modelKey) {
    if (modelKey === 'ecmwf_cim_wrf3' || modelKey === 'icon_cim_wrf3') {
        return 'cim';
    }
    // ... lógica existente ...
}
```

### 4. Configurar fontes de dados
```javascript
const WRF_PUBLISHED_SOURCES = {
    // ... existentes ...
    'ecmwf_cim_wrf3': {
        root: 'https://raw.githubusercontent.com/SEU_USUARIO/sideral-meteorologia/cim-wrf3-ecmwf-data/',
        branch: 'cim-wrf3-ecmwf-data',
        modelLabel: 'ECMWF → CIM 3km'
    },
    'icon_cim_wrf3': {
        root: 'https://raw.githubusercontent.com/SEU_USUARIO/sideral-meteorologia/cim-wrf3-icon-data/',
        branch: 'cim-wrf3-icon-data',
        modelLabel: 'ICON → CIM 3km'
    }
};
```

### 5. Atualizar nomes
```javascript
const modelNames = {
    // ... existentes ...
    'ecmwf_cim_wrf3': 'ECMWF → CIM WRF 3 KM',
    'icon_cim_wrf3': 'ICON → CIM WRF 3 KM'
};
```

---

## 📊 Estrutura de Arquivos Gerados

### Branch `cim-wrf3-ecmwf-data`
```
metadata.json          # Metadados da rodada
f000.json.gz           # F000 (análise inicial)
f003.json.gz           # F003 (+3 horas)
f006.json.gz           # F006 (+6 horas)
...
f036.json.gz           # F036 (+36 horas)
```

### Conteúdo do metadata.json
```json
{
  "product": "CIM WRF 3 KM",
  "domain": "cim",
  "resolutionKm": 3,
  "model": "ecmwf",
  "initTime": "2026-08-13T06:00:00Z",
  "runCycle": "06z",
  "status": "complete",
  "reflectivitySource": "REFL_10CM_NATIVE",
  "frames": [
    {"forecastHour": 0, "validTime": "2026-08-13T06:00:00Z", "file": "f000.json.gz"},
    {"forecastHour": 3, "validTime": "2026-08-13T09:00:00Z", "file": "f003.json.gz"},
    ...
  ],
  "generatedAt": "2026-08-13T07:30:00Z"
}
```

---

## ⚠️ Solução de Problemas

### Container falha no build
- Verifique se tem Docker Desktop ou Docker Engine atualizado
- Aumente memória disponível para Docker (mínimo 8GB)
- Execute `docker builder prune` para limpar cache

### Workflow falha em "Run geogrid.exe"
- Verifique se os dados geográficos foram baixados corretamente
- Confirme que o caminho `/geog` existe no container
- Logs detalhados estão nos artifacts do workflow

### Workflow falha em "Run wrf.exe"
- Grade CIM (1801×1401) requer memória significativa
- Aumentei `--shm-size=4g` no container
- Se persistir, reduza `e_we`/`e_sn` no `namelist.input.cim`

### Frames não aparecem no frontend
- Verifique se as branches de dados foram criadas e têm push
- Confirme que `metadata.json` aponta para arquivos existentes
- Teste URLs diretamente: `https://raw.githubusercontent.com/SEU_USUARIO/sideral-meteorologia/cim-wrf3-ecmwf-data/metadata.json`

---

## 📈 Monitoramento

### Verificar status dos workflows
```bash
gh run list --workflow="CIM WRF 3 KM - ECMWF" --limit 5
gh run view <RUN_ID> --log
```

### Verificar última rodada publicada
```bash
curl -s https://raw.githubusercontent.com/SEU_USUARIO/sideral-meteorologia/cim-wrf3-ecmwf-data/metadata.json | jq
```

---

## 🎯 Próximos Passos Após Setup

1. ✅ Executar teste manual (F000-F006)
2. ✅ Validar frames gerados
3. ✅ Integrar frontend
4. ✅ Monitorar primeira execução automática
5. ✅ Ajustar horizonte de previsão (atualmente 36h)

---

## 📞 Suporte

Documentação adicional:
- `docs/CIM_WRF3_KM.md` - Detalhes técnicos do modelo
- `docs/frontend_integration_guide.md` - Guia completo de frontend
- `IMPLEMENTACAO_FINAL_CIM_WRF3.md` - Resumo da implementação

**Importante**: A primeira execução pode levar até 2 horas devido ao download de dados e compilação JIT no container. Execuções subsequentes são mais rápidas devido ao cache.
