# Guia de Integração Frontend - CIM WRF 3 KM

Este documento descreve as alterações necessárias no frontend (`refletividaded.html`) para integrar o novo modelo CIM WRF 3 KM.

## 1. Adicionar Grupo no Select de Modelos

No `<select id="modelSelect">`, adicionar:

```html
<optgroup label="CIM WRF 3 KM — Sul / Paraguai / Uruguai / Argentina">
    <option value="ecmwf_cim_wrf3">ECMWF → CIM WRF 3 KM</option>
    <option value="icon_cim_wrf3">ICON → CIM WRF 3 KM</option>
</optgroup>
```

**Importante**: NÃO adicionar GFS neste grupo.

## 2. Adicionar Domínio CIM nas Configurações

Adicionar um terceiro domínio além de `sul` e `sudeste`:

```javascript
const MODEL_DOMAIN_BOUNDS = {
    sul: {
        bounds: [[-34.5, -57.0], [-24.0, -46.0]],
        label: 'WRF Sul 4 km',
        info: 'Região Sul do Brasil'
    },
    sudeste: {
        bounds: [[-26.0, -53.0], [-18.0, -40.0]],
        label: 'WRF Sudeste 4 km',
        info: 'Região Sudeste do Brasil'
    },
    cim: {
        bounds: [[-40.0, -65.0], [-19.0, -47.0]],
        label: 'CIM WRF 3 KM · Sul / Paraguai / Uruguai / Argentina',
        info: 'Domínio Cone Sul - Resolução 3 km'
    }
};
```

## 3. Atualizar domainKeyForModel()

A função que mapeia modelo para domínio deve reconhecer os novos modelos:

```javascript
function domainKeyForModel(modelKey) {
    if (modelKey === 'ecmwf_cim_wrf3' || modelKey === 'icon_cim_wrf3') {
        return 'cim';
    }
    // ... lógica existente para outros modelos
}
```

**Importante**: Não deixar CIM cair no fallback `'sul'`, pois isso cortaria grande parte do domínio.

## 4. Atualizar backendModelKey()

Para identificar a fonte dos dados:

```javascript
function backendModelKey(modelKey) {
    if (modelKey === 'ecmwf_cim_wrf3') {
        return 'ecmwf';
    }
    if (modelKey === 'icon_cim_wrf3') {
        return 'icon';
    }
    // ... fallback existente
}
```

**Importante**: Não deixar nenhum CIM virar `gfs` pelo fallback.

## 5. Adicionar Modelos Permitidos

Na lista `allowed` dentro de `resolveModelForVariable()`:

```javascript
const allowed = [
    // ... modelos existentes
    'ecmwf_cim_wrf3',
    'icon_cim_wrf3'
];
```

**Atenção**: CIM WRF 3 KM NÃO é WRF 2. Não transformar automaticamente `ecmwf_cim_wrf3` em `ecmwf_wrf2_sudeste`.

Para variáveis exclusivas do WRF2 que o CIM ainda não publica, desabilitar a variável ou mostrar mensagem clara de indisponibilidade.

## 6. Adicionar Fontes de Dados Publicados

No mapa `WRF_PUBLISHED_SOURCES`:

```javascript
const WRF_PUBLISHED_SOURCES = {
    // ... fontes existentes
    
    ecmwf_cim_wrf3: {
        root: 'https://raw.githubusercontent.com/SEU_REPOSITORIO/sideral-backend',
        branch: 'cim-wrf3-ecmwf-data'
    },
    
    icon_cim_wrf3: {
        root: 'https://raw.githubusercontent.com/SEU_REPOSITORIO/sideral-backend',
        branch: 'cim-wrf3-icon-data'
    }
};
```

**Verificar** o repositório correto antes de gravar a URL.

## 7. Atualizar Nomes no Header (drawHeader)

Para exibir corretamente nos PNGs/GIFs:

```javascript
const modelNames = {
    // ... nomes existentes
    
    'ecmwf_cim_wrf3': 'ECMWF → CIM WRF 3 KM',
    'icon_cim_wrf3': 'ICON → CIM WRF 3 KM'
};
```

O cabeçalho deve deixar claro que é **CIM WRF 3 KM** e qual foi a condição inicial (ECMWF ou ICON).

## 8. Refatorar Labels de Produtos

Se houver lógica que assume apenas "Sul 4 km" ou "Sudeste 4 km", refatorar para suportar:

- Sul 4 km
- Sudeste 4 km
- CIM 3 km

Exemplo:

```javascript
function getProductLabel(modelKey) {
    if (modelKey === 'ecmwf_cim_wrf3' || modelKey === 'icon_cim_wrf3') {
        return 'CIM WRF 3 KM';
    }
    // ... lógica existente
}
```

Não produzir texto "CIM 4 km" por herdar hardcode antigo.

## 9. Mapa - Centralização Automática

Ao selecionar CIM:

1. Desenhar retângulo do domínio CIM
2. Centralizar automaticamente o mapa
3. Mostrar todo o domínio (não apenas Brasil)
4. Incluir fronteiras internacionais
5. Manter estados brasileiros
6. Mostrar corretamente Paraguai, Uruguai e Argentina
7. Não recortar dados na fronteira

O produto meteorológico deve continuar até o limite real da grade WRF, mesmo fora do Brasil.

## 10. Grid de Renderização

Não confundir:

- **Resolução do WRF** = 3 km (dx=dy=3000 no namelist.input)
- **Resolução gráfica do canvas** = RENDER_GRID_X / RENDER_GRID_Y

Aumentar RENDER_GRID_X/Y não cria WRF de maior resolução. É apenas interpolação visual.

O CIM só é 3 km porque o `namelist.input` realmente usa dx=dy=3000 e o `wrfout` foi produzido nessa grade.

## 11. Compressão JSON

Manter compatibilidade com carregamento JSON GZIP existente.

Não enviar NetCDF inteiro para o navegador. O pós-processador extrai somente campos necessários.

Se necessário para performance:
- Reduzir precisão excessiva de floats
- Usar arrays compactos
- Gzip
- Evitar propriedades repetidas

**NÃO** reduzir a resolução meteorológica para economizar JSON. A compactação é no formato de transporte.

## 12. Timeline

A timeline deve utilizar somente horários realmente publicados conforme metadata.json.

Se metadata tem frames F000, F003, F006...F036, a timeline mostra apenas esses.

## 13. Teste de Troca de Modelo

Testar mudança CIM → WRF Sul → CIM para confirmar que nenhum estado fica preso em cache.

Cada modelo deve carregar seus próprios frames sem interferência.

## 14. Tratamento de Indisponibilidade

Se uma variável não estiver disponível no CIM (ex: alguma específica do WRF2):

- Desabilitar a variável no UI, OU
- Mostrar mensagem clara: "Variável X indisponível para CIM WRF 3 KM"

Não tentar fallback silencioso para outro modelo.

---

## Resumo das Chaves

| Chave do Modelo | Label no Select | Domínio | Fonte | Branch |
|-----------------|-----------------|---------|-------|--------|
| `ecmwf_cim_wrf3` | ECMWF → CIM WRF 3 KM | cim | ecmwf | cim-wrf3-ecmwf-data |
| `icon_cim_wrf3` | ICON → CIM WRF 3 KM | cim | icon | cim-wrf3-icon-data |
