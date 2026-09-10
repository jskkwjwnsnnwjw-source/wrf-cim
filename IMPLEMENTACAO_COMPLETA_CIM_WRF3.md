# CIM WRF 3 KM - Implementação Completa

## Resumo

Implementação completa do novo modelo regional **CIM WRF 3 KM** para a Sideral Meteorologia, cobrindo o Cone Sul com resolução de 3 km.

## Arquivos Criados

### Container Docker
- `Dockerfile.wrf` - WRF 4.4.0 + WPS 4.4.0 compilados automaticamente

### Workflows GitHub Actions
- `.github/workflows/cim-wrf3-ecmwf.yml` - ECMWF → CIM (agendado 06z,08z,12z,18z,21z)
- `.github/workflows/cim-wrf3-icon.yml` - ICON → CIM (agendado 06z,08z,12z,18z,21z)

### Scripts Python
- `scripts/download_ecmwf.py` - Download ECMWF Open Data (sem API key)
- `scripts/download_icon.py` - Download ICON DWD Open Data
- `scripts/postprocess_cim.py` - wrfout → frames JSON.GZ
- `scripts/validate_cim_wrf3.py` - Validação antes da publicação

### Scripts Bash
- `scripts/build_and_push_container.sh` - Build e push do container Docker
- `scripts/create_data_branches.sh` - Cria branches de dados

### Configuração WRF
- `config/cim/namelist.wps.cim` - Configuração WPS (geogrid, metgrid)
- `config/cim/namelist.input.cim` - Configuração WRF (real, wrf)
- `config/cim/domain_config.json` - Metadados do domínio
- `config/cim/example_metadata.json` - Exemplo de metadata.json

---

## Domínio Configurado

| Parâmetro | Valor |
|-----------|-------|
| **Limites** | Sul: -40.0°, Norte: -19.0°, Oeste: -65.0°, Leste: -47.0° |
| **Projeção** | Lambert Conformal |
| **ref_lat / ref_lon** | -29.5° / -56.0° |
| **truelat1 / truelat2** | -25.0° / -33.0° |
| **stand_lon** | -56.0° |
| **e_we × e_sn** | 1801 × 1401 = 2.523.201 células |
| **dx / dy** | 3000 m / 3000 m (verdadeiros 3 km) |
| **Níveis verticais** | 50 |
| **Time step** | 18 segundos |

### Cobertura Geográfica
- Paraná, Santa Catarina, Rio Grande do Sul
- Paraguai (todo)
- Uruguai (todo)
- Nordeste e parte central da Argentina

---

## Física WRF

| Esquema | Opção | Descrição |
|---------|-------|-----------|
| Microfísica | `mp_physics = 8` | Morrison double-moment |
| Radiação LW | `ra_lw_physics = 1` | RRTM |
| Radiação SW | `ra_sw_physics = 2` | Dudhia |
| PBL | `bl_pbl_physics = 1` | YSU |
| Camada Superficial | `sf_sfclay_physics = 1` | Monin-Obukhov |
| Cumulus | `cu_physics = 0` | **Desativado** (convecção explícita) |

---

## Como Usar

### Passo 1: Build do Container Docker

```bash
cd /workspace
chmod +x scripts/build_and_push_container.sh

# Definir token do GitHub (necessário para push)
export GHCR_TOKEN="seu_token_aqui"

# Executar build (20-40 minutos)
./scripts/build_and_push_container.sh
```

Isso criará a imagem `ghcr.io/SEU_USUARIO/wrf-cim-container:latest`.

### Passo 2: Criar Branches de Dados

```bash
chmod +x scripts/create_data_branches.sh
./scripts/create_data_branches.sh
```

Isso criará:
- `cim-wrf3-ecmwf-data`
- `cim-wrf3-icon-data`

### Passo 3: Atualizar Workflows (se necessário)

Os workflows já estão configurados para usar:
```yaml
CONTAINER_IMAGE: ghcr.io/${{ github.repository_owner }}/wrf-cim-container:latest
```

Certifique-se de que o container foi pushado para este repositório.

### Passo 4: Testar Manualmente

No GitHub:
1. Vá em **Actions** → **CIM WRF 3 KM - ECMWF**
2. Clique em **Run workflow**
3. Selecione **Test run: true** (F000-F006 apenas)
4. Execute

### Passo 5: Integração Frontend

Edite `refletividaded.html` conforme descrito em `FRONTEND_INTEGRATION.md`:

1. Adicionar opções no `<select>`:
```html
<optgroup label="CIM WRF 3 KM — Sul / Paraguai / Uruguai / Argentina">
    <option value="ecmwf_cim_wrf3">ECMWF → CIM WRF 3 KM</option>
    <option value="icon_cim_wrf3">ICON → CIM WRF 3 KM</option>
</optgroup>
```

2. Adicionar domínio `cim` em `MODEL_DOMAIN_BOUNDS`
3. Atualizar `domainKeyForModel()`, `backendModelKey()`
4. Configurar `WRF_PUBLISHED_SOURCES`

---

## Agendamento Automático

Os workflows rodam automaticamente todos os dias às:
- **06:15 UTC** (dados 06z)
- **08:15 UTC** (dados 08z - extra)
- **12:15 UTC** (dados 12z)
- **18:15 UTC** (dados 18z)
- **21:15 UTC** (dados 21z - extra)

O atraso de 15 minutos garante que os dados das fontes estejam disponíveis.

---

## Fontes de Dados

### ECMWF Open Data
- URL: `https://data.ecmwf.int/forecasts/`
- Formato: GRIB2
- Resolução: 0.25° (~25 km)
- **Não requer API key**
- Disponível para: 00z, 06z, 12z, 18z

### ICON DWD
- URL: `https://opendata.dwd.de/weather/nwp/icon/grib/`
- Formato: GRIB2 (compressão bz2)
- Resolução: ~13 km (global)
- **Dados públicos**
- Disponível para: 00z, 06z, 12z, 18z

---

## Estrutura de Publicação

Cada branch de dados contém:
```
cim-wrf3-ecmwf-data/
├── metadata.json
├── f000.json.gz
├── f003.json.gz
├── f006.json.gz
├── ...
└── f036.json.gz
```

### metadata.json
```json
{
  "product": "CIM WRF 3 KM",
  "domain": "cim",
  "resolutionKm": 3,
  "model": "ecmwf",
  "initTime": "2024-01-15T12:00:00Z",
  "runCycle": "12z",
  "status": "complete",
  "reflectivitySource": "REFL_10CM_NATIVE",
  "frameCount": 13,
  "frames": [...]
}
```

---

## Variáveis Publicadas

| Variável | Campo WRF | Descrição |
|----------|-----------|-----------|
| `temperature_2m` | T2 | Temperatura a 2m (°C) |
| `humidity_2m` | RH2 | Umidade relativa a 2m (%) |
| `wind_u_10m` | U10 | Componente U do vento a 10m (m/s) |
| `wind_v_10m` | V10 | Componente V do vento a 10m (m/s) |
| `precipitation` | RAINNC + RAINC | Precipitação acumulada (mm) |
| `reflectivity` | REFL_10CM | Refletividade simulada (dBZ) |
| `mucape` | MUCAPE | CAPE mais instável (J/kg) |

---

## Validação

O script `validate_cim_wrf3.py` verifica:
- [x] metadata.json existe e é válido
- [x] domain == "cim"
- [x] resolutionKm == 3
- [x] model é "ecmwf" ou "icon"
- [x] status == "complete"
- [x] Todos os frames existem
- [x] forecastHour corresponde ao arquivo
- [x] Grid não está vazio
- [x] Sem NaN/Infinity nos campos

---

## Limitações e Considerações

### Recursos Necessários
- **RAM**: Mínimo 16GB (recomendado 32GB+) para grade 1801×1401
- **CPU**: 4+ núcleos para execução paralela (MPI)
- **Disco**: ~50GB livres por rodada (dados temporários + saída)
- **Tempo**: ~2-4 horas para previsão de 36h no GitHub Actions

### Otimizações
- geogrid pode ser cacheado (domínio fixo)
- Frames são comprimidos com gzip (redução ~80%)
- Apenas variáveis essenciais são extraídas

### Convecção Explícita
- `cu_physics = 0` significa que convecção é resolvida explicitamente
- Adequado para resolução de 3 km
- Pode exigir time step menor (18s configurado)

---

## Solução de Problemas

### geogrid falha
- Verificar se `geog_data_path` está correto no namelist
- Confirmar que dados geográficos foram baixados

### ungrib falha
- Verificar formato dos arquivos GRIB2
- Confirmar que variáveis necessárias estão presentes

### real.exe falha
- Checar logs `rsl.error.*`
- Verificar compatibilidade entre metgrid e boundary

### wrf.exe falha
- Aumentar `time_step` se houver erro CFL
- Verificar memória disponível

### Publicação falha
- Confirmar token do GitHub com permissão de write
- Verificar se branches de dados existem

---

## Próximos Passos

1. ✅ Todos os arquivos criados
2. ⏳ Executar `build_and_push_container.sh`
3. ⏳ Executar `create_data_branches.sh`
4. ⏳ Testar workflow manual (test_run=true)
5. ⏳ Integrar frontend (`refletividaded.html`)
6. ⏳ Monitorar primeira execução automática

---

## Documentação Adicional

- `docs/CIM_WRF3_KM.md` - Detalhes técnicos do modelo
- `docs/frontend_integration_guide.md` - Guia de integração frontend
- `config/cim/domain_config.json` - Configuração completa do domínio

---

**Status**: Infraestrutura pronta. Pendências: build do container, criação de branches, integração frontend.
