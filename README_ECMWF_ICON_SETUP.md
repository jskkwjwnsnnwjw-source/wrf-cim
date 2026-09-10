# Instalação e Uso dos Downloaders ECMWF e ICON

## Visão Geral

Dois scripts Python foram implementados para baixar dados de condições iniciais para o CIM WRF 3 KM:

1. `scripts/download_ecmwf.py` - Dados do ECMWF (via CDS API)
2. `scripts/download_icon.py` - Dados do ICON (via DWD OpenData)

---

## ECMWF

### Pré-requisitos

```bash
pip install cdsapi requests numpy
```

### Configuração da API

Crie o arquivo `~/.cdsapirc`:

```
url: https://cds.climate.copernicus.eu/api/v2
key: SEU_UID:SUA_CHAVE_API
```

Para obter sua chave:
1. Acesse https://cds.climate.copernicus.eu/
2. Faça login ou crie uma conta
3. Vá em "Your API key"
4. Copie UID e chave

### Uso Básico

```bash
# Teste rápido (apenas 1 variável, F000)
python3 scripts/download_ecmwf.py \
    --init-time "2024-01-15T12:00:00Z" \
    --hours "0" \
    --output-dir /tmp/ecmwf_data \
    --test-mode

# Download completo (F000-F036)
python3 scripts/download_ecmwf.py \
    --init-time "2024-01-15T12:00:00Z" \
    --hours "0,3,6,9,12,15,18,21,24,27,30,33,36" \
    --output-dir /data/ecmwf_cim_wrf3/20240115_12
```

### Variáveis Baixadas

**Superfície:**
- 10m_u_component_of_wind
- 10m_v_component_of_wind
- 2m_temperature
- 2m_dewpoint_temperature
- mean_sea_level_pressure
- surface_pressure
- skin_temperature
- soil_temperature_level_* (1-4)
- volumetric_soil_water_layer_* (1-4)

**Níveis de Pressão (1000-10 hPa):**
- geopotential
- temperature
- u_component_of_wind
- v_component_of_wind
- relative_humidity
- specific_humidity

---

## ICON

### Pré-requisitos

```bash
pip install requests cfgrib eccodes
```

### Uso Básico

```bash
# Teste rápido (apenas t_2m, F000)
python3 scripts/download_icon.py \
    --init-time "2026-09-10T00:00:00Z" \
    --hours "0" \
    --output-dir /tmp/icon_data \
    --test-mode

# Download completo
python3 scripts/download_icon.py \
    --init-time "2026-09-10T00:00:00Z" \
    --hours "0,3,6,9,12,15,18,21,24,27,30,33,36" \
    --output-dir /data/icon_cim_wrf3/20260910_00
```

### URLs Reais

O script usa o formato confirmado do DWD:

```
https://opendata.dwd.de/weather/nwp/icon/grib/{HH}/{var}/icon_global_icosahedral_single-level_{YYYYMMDD}{HH}_{FFF}_{VAR}.grib2.bz2
```

Exemplo real testado:
```
https://opendata.dwd.de/weather/nwp/icon/grib/00/t_2m/icon_global_icosahedral_single-level_2026091000_000_T_2M.grib2.bz2
```

### Variáveis Baixadas

**Single-level:**
- t_2m (temperatura a 2m)
- u_10m, v_10m (vento a 10m)
- pmsl (pressão ao nível do mar)
- pres_sfc (pressão de superfície)

**Pressure-levels (opcional):**
- gh (geopotencial)
- t (temperatura)
- u, v (vento)
- rh (umidade relativa)

---

## Formato dos Arquivos

### ECMWF
- Formato: GRIB
- Um arquivo por variável
- Contém todos os forecast hours no mesmo arquivo

### ICON
- Formato: GRIB2 (comprimido com bz2)
- Um arquivo por variável por forecast hour
- Descomprimido automaticamente pelo script

---

## Validação

Verifique os arquivos baixados:

```bash
# ECMWF
ls -lh /tmp/ecmwf_data/*.grib

# ICON
ls -lh /tmp/icon_data/*.grib2

# Ler com cfgrib (ICON)
python3 -c "
import cfgrib
ds = cfgrib.open_dataset('/tmp/icon_data/t_2m_*.grib2')
print(ds.data_vars)
print(ds['t2m'].shape)
"
```

---

## Integração com WPS/WRF

Após download:

1. **ECMWF**: Use `ungrib.exe` com Vtable apropriado
2. **ICON**: Use `metgrid.exe` diretamente (já está em grade regular após interpolação)

Os arquivos devem estar em diretórios separados por init time:

```
/data/cim-wrf3/
├── ecmwf/
│   └── 20240115_12/
│       ├── 2m_temperature_2024-01-15_12:00.grib
│       └── ...
└── icon/
    └── 20260910_00/
        ├── t_2m_20260910_00_000.grib2
        └── ...
```

---

## Limitações

### ECMWF
- Requer conta CDS registrada
- Limite de downloads por hora/dia
- Delay de disponibilidade (~5 dias para reanálise)

### ICON
- Grade icosaédrica não estruturada (requer interpolação)
- Dados disponíveis apenas para rodadas recentes
- Arquivos grandes (~3MB por variável por hora)

---

## Troubleshooting

### Erro: "Missing CDS API key"
```bash
cat ~/.cdsapirc
# Deve conter url e key válidos
```

### Erro: "404 Not Found" (ICON)
- Verifique se a rodada está disponível
- Rodadas ICON: 00, 06, 12, 18 UTC
- Dados disponíveis ~2-3 horas após inicialização

### Erro: "Connection timeout"
- Aumente timeout no script
- Verifique conectividade
- Use proxy se necessário

---

## Próximos Passos

1. Baixar dados completos (todas variáveis)
2. Executar WPS (geogrid, ungrib/metgrid)
3. Executar real.exe
4. Executar wrf.exe
5. Pós-processar wrfout
6. Publicar frames

Ver workflows em `.github/workflows/cim-wrf3-*.yml` para automação completa.
