# CIM WRF 3 KM

Modelo regional de alta resolução (3 km) executado pela infraestrutura da Sideral/CIM.

## Domínio

O CIM WRF 3 KM cobre o Cone Sul relevante para a meteorologia da Região Sul do Brasil:

- **Região Sul do Brasil**: Paraná, Santa Catarina, Rio Grande do Sul
- **Paraguai**: todo o território
- **Uruguai**: todo o território
- **Argentina**: nordeste, leste e parte central (necessária para acompanhamento de sistemas)

### Coordenadas do Domínio

| Parâmetro | Valor |
|-----------|-------|
| Limite Sul | -40.0° |
| Limite Norte | -19.0° |
| Limite Oeste | -65.0° |
| Limite Leste | -47.0° |
| Latitude de referência | -29.5° |
| Longitude de referência | -56.0° |
| Projeção | Lambert Conformal |
| True Lat 1 | -25.0° |
| True Lat 2 | -33.0° |

### Grade

| Parâmetro | Valor |
|-----------|-------|
| Resolução horizontal | 3 km |
| dx | 3000 m |
| dy | 3000 m |
| e_we | 1801 pontos |
| e_sn | 1401 pontos |
| e_vert | 50 níveis verticais |
| Total de células | ~2.5 milhões |

## Condições Iniciais e de Contorno

O CIM WRF 3 KM é inicializado a partir de **dois** conjuntos de dados globais:

1. **ECMWF** → CIM WRF 3 KM (`ecmwf_cim_wrf3`)
2. **ICON** → CIM WRF 3 KM (`icon_cim_wrf3`)

**NÃO há versão GFS do CIM.**

### Frequência de Inicialização

- ECMWF: 00, 06, 12, 18 UTC
- ICON: 00, 06, 12, 18 UTC

## Horizonte de Previsão

Previsão até **36 horas** com saída a cada **3 horas**:

F000, F003, F006, F009, F012, F015, F018, F021, F024, F027, F030, F033, F036

## Variáveis Publicadas

| Variável | Descrição | Origem |
|----------|-----------|--------|
| Refletividade | Reflectivity 10 cm | REFL_10CM_NATIVE (WRF) |
| Precipitação | Acumulada | Microfísica WRF |
| MUCAPE/CAPE | Energia convectiva | Derivado do WRF |
| Vento | Zonal e Meridional | WRF nativo |
| Temperatura | Em níveis | WRF nativo |
| Umidade | Relativa | WRF nativo |
| Bulk Shear | 0-6 km | Calculado |

## Configuração Física

| Esquema | Opção | Descrição |
|---------|-------|-----------|
| Microfísica | 8 | Morrison double-moment |
| Radiação LW | 1 | RRTM |
| Radiação SW | 2 | Dudhia |
| Camada de Superfície | 1 | Monin-Obukhov |
| Física de Superfície | 2 | Noah LSM |
| PBL | 1 | Yonsei University (YSU) |
| Cumulus | 0 | **Desativado** (resolução explícita) |

**Nota**: A parametrização convectiva é desativada porque a resolução de 3 km permite convecção explícita.

## Formato dos Arquivos

### Estrutura de Publicação

```
cim-wrf3-ecmwf-data/          # Branch para ECMWF
├── metadata.json
└── frames/
    ├── f000.json.gz
    ├── f003.json.gz
    ├── f006.json.gz
    └── ...

cim-wrf3-icon-data/           # Branch para ICON
├── metadata.json
└── frames/
    ├── f000.json.gz
    ├── f003.json.gz
    └── ...
```

### metadata.json

```json
{
  "product": "CIM WRF 3 KM",
  "domain": "cim",
  "resolutionKm": 3,
  "model": "ecmwf",
  "modelKey": "ecmwf_cim_wrf3",
  "initTime": "2024-01-15T12:00:00Z",
  "runCycle": "2024-01-15T12:30:00Z",
  "status": "complete",
  "reflectivitySource": "REFL_10CM_NATIVE",
  "frames": [
    {"forecastHour": 0, "validTime": "...", "file": "frames/f000.json.gz"},
    {"forecastHour": 3, "validTime": "...", "file": "frames/f003.json.gz"}
  ]
}
```

### Frames

Cada frame é um arquivo JSON comprimido com gzip contendo:

- `forecastHour`: Hora de previsão (0, 3, 6, ...)
- `validTime`: Tempo válido em ISO 8601
- `domain`: "cim"
- `resolutionKm`: 3
- `grid`: Informações da grade (e_we, e_sn, dx, dy)
- `data`: Campos meteorológicos

## Como Iniciar Manualmente

### Via GitHub Actions

1. Acesse a aba **Actions** no repositório
2. Selecione **CIM WRF 3 KM - ECMWF** ou **CIM WRF 3 KM - ICON**
3. Clique em **Run workflow**
4. Preencha:
   - **Initial time**: (opcional) YYYY-MM-DDTHH:00:00Z
   - **Forecast hours**: (opcional) ex: `0,3,6` para teste
5. Execute

### Teste Rápido

Para teste, use apenas F000-F006:

```
Forecast hours: 0,3,6
```

Isso processa apenas 3 horas de previsão para validação rápida antes de executar o ciclo completo.

## Limitações

1. **Peso computacional**: O domínio de ~2.5 milhões de células em 3 km requer recursos significativos. Rodadas completas (36h) podem demorar várias horas.

2. **Disponibilidade dos dados globais**: O CIM depende da disponibilidade tempestiva do ECMWF e ICON. Se houver atraso nas condições de contorno, o CIM também atrasará.

3. **Armazenamento**: Cada rodada completa gera aproximadamente X GB de dados brutos (wrfout). Os frames publicados são significativamente menores graças à compressão e extração seletiva de variáveis.

4. **Convecção explícita**: Embora a resolução de 3 km permita convecção explícita, processos de escala muito fina ainda podem ser sub-resolvidos.

5. **Fronteira oeste**: O limite em -65.0° pode cortar sistemas que vêm dos Andes. Esta é uma limitação conhecida do domínio atual.

## Validação

Antes da publicação, cada rodada passa por validação automática:

- [x] Domain = "cim"
- [x] ResolutionKm = 3
- [x] dx = dy = 3000
- [x] Model = ecmwf ou icon (nunca gfs)
- [x] Todos os frames existem
- [x] forecastHour consistente
- [x] validTime coerente com initTime
- [x] Sem NaN/Infinity nos dados
- [x] Refletividade com origem correta

Script de validação: `scripts/validate_cim_wrf3.py`

## Identificadores

| Chave | Descrição |
|-------|-----------|
| `ecmwf_cim_wrf3` | ECMWF → CIM WRF 3 KM |
| `icon_cim_wrf3` | ICON → CIM WRF 3 KM |

**Não usar** `ecmwf_wrf`, `icon_wrf`, `ecmwf_wrf_sudeste` etc. para o CIM.

## Diferenças para Outros WRF

| Característica | CIM 3 KM | WRF Sul 4 KM | WRF Sudeste 4 KM |
|----------------|----------|--------------|------------------|
| Domínio | Cone Sul | Sul Brasil | Sudeste Brasil |
| Resolução | 3 km | 4 km | 4 km |
| Fontes | ECMWF, ICON | (ver config) | (ver config) |
| Convecção | Explícita | (ver config) | (ver config) |

## Histórico

- **2024**: Implementação inicial do CIM WRF 3 KM
- Domínio otimizado para capturar sistemas antes de entrarem no Sul do Brasil

---

**Nota**: CIM WRF 3 KM é uma configuração regional do WRF executada pela infraestrutura da Sideral/CIM, inicializada a partir de dados ECMWF ou ICON. Não é um modelo independente, mas sim uma aplicação específica do WRF-ARW com domínio e configuração próprios.
