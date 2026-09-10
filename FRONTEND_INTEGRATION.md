# Guia de Integração Frontend - CIM WRF 3 KM

## Resumo

Este guia descreve as alterações necessárias no `refletividaded.html` para integrar o novo modelo CIM WRF 3 KM.

---

## 1. Adicionar Opções no Select de Modelos

Localize o elemento `<select id="modelSelect">` e adicione:

```html
<optgroup label="CIM WRF 3 KM — Sul / Paraguai / Uruguai / Argentina">
    <option value="ecmwf_cim_wrf3">ECMWF → CIM WRF 3 KM</option>
    <option value="icon_cim_wrf3">ICON → CIM WRF 3 KM</option>
</optgroup>
```

**Importante**: Não adicionar GFS neste grupo.

---

## 2. Adicionar Domínio CIM

No JavaScript, localize `MODEL_DOMAIN_BOUNDS` e adicione:

```javascript
const MODEL_DOMAIN_BOUNDS = {
    // ... domínios existentes (sul, sudeste) ...
    
    'cim': {
        bounds: [
            [-40.0, -65.0],  // Sudoeste (Argentina/Sul BR)
            [-19.0, -47.0]   // Nordeste (Mato Grosso/Atlântico)
        ],
        label: 'CIM · Sul / PY / UY / AR',
        center: [-29.5, -56.0],
        zoom: 6,
        info: 'CIM WRF 3 KM - Cone Sul (Paraná, SC, RS, Paraguai, Uruguai, Argentina)'
    }
};
```

---

## 3. Atualizar domainKeyForModel()

Localize a função `domainKeyForModel(modelKey)` e adicione:

```javascript
function domainKeyForModel(modelKey) {
    // Novos modelos CIM
    if (modelKey === 'ecmwf_cim_wrf3' || modelKey === 'icon_cim_wrf3') {
        return 'cim';
    }
    
    // ... lógica existente para outros modelos ...
    
    // Fallback
    return 'sul';
}
```

**Importante**: Não deixar CIM cair no fallback `'sul'`, pois os bounds são diferentes.

---

## 4. Atualizar backendModelKey()

Adicione mapeamento para os novos modelos:

```javascript
function backendModelKey(modelKey) {
    // CIM WRF 3 KM
    if (modelKey === 'ecmwf_cim_wrf3') {
        return 'ecmwf';
    }
    if (modelKey === 'icon_cim_wrf3') {
        return 'icon';
    }
    
    // ... lógica existente ...
    
    return modelKey;
}
```

---

## 5. Configurar WRF_PUBLISHED_SOURCES

Adicione as fontes de dados do CIM:

```javascript
const WRF_PUBLISHED_SOURCES = {
    // ... fontes existentes ...
    
    'ecmwf_cim_wrf3': {
        root: 'https://raw.githubusercontent.com/',
        branch: 'cim-wrf3-ecmwf-data',
        path: '/',
        modelLabel: 'ECMWF → CIM WRF 3 KM',
        domain: 'cim',
        resolutionKm: 3
    },
    
    'icon_cim_wrf3': {
        root: 'https://raw.githubusercontent.com/',
        branch: 'cim-wrf3-icon-data',
        path: '/',
        modelLabel: 'ICON → CIM WRF 3 KM',
        domain: 'cim',
        resolutionKm: 3
    }
};
```

**Nota**: Substitua a URL base pela correta do seu repositório.

---

## 6. Atualizar Lista de Modelos Permitidos

Localize `resolveModelForVariable()` ou similar e adicione aos allowed:

```javascript
const allowedModels = [
    // ... modelos existentes ...
    'ecmwf_cim_wrf3',
    'icon_cim_wrf3'
];
```

**Importante**: CIM WRF 3 KM NÃO é WRF 2. Não transformar automaticamente em `ecmwf_wrf2_sudeste`.

---

## 7. Atualizar Nomes dos Modelos (Header)

Atualize `modelNames` ou `drawHeader()`:

```javascript
const modelNames = {
    // ... nomes existentes ...
    
    'ecmwf_cim_wrf3': 'ECMWF → CIM WRF 3 KM',
    'icon_cim_wrf3': 'ICON → CIM WRF 3 KM'
};
```

---

## 8. Atualizar Labels de Produto

Se houver função que monta nomes de produto, adicione suporte a:

```javascript
function getProductLabel(modelKey, resolution) {
    if (modelKey === 'ecmwf_cim_wrf3' || modelKey === 'icon_cim_wrf3') {
        return 'CIM 3 km';
    }
    
    // ... lógica existente para Sul 4km, Sudeste 4km ...
}
```

---

## 9. Centralizar Mapa Automaticamente

Quando o usuário selecionar CIM, centralizar o mapa:

```javascript
function onModelChange(modelKey) {
    const domainKey = domainKeyForModel(modelKey);
    
    if (domainKey === 'cim') {
        map.setView(MODEL_DOMAIN_BOUNDS['cim'].center, MODEL_DOMAIN_BOUNDS['cim'].zoom);
        drawDomainBounds('cim');
    }
    
    // ... resto da lógica ...
}
```

---

## 10. Desenhar Retângulo do Domínio

Adicionar função para desenhar bounds do domínio CIM:

```javascript
function drawDomainBounds(domainKey) {
    const bounds = MODEL_DOMAIN_BOUNDS[domainKey];
    if (!bounds) return;
    
    // Remover bounds anteriores
    if (window.domainRectangle) {
        window.domainRectangle.remove();
    }
    
    // Desenhar novo retângulo
    window.domainRectangle = L.rectangle(bounds.bounds, {
        color: '#ff0000',
        weight: 2,
        fillOpacity: 0.1
    }).addTo(map);
}
```

---

## 11. Testes de Validação Frontend

Após as alterações, testar:

1. **Selecionar ECMWF → CIM 3 KM**
   - Mapa deve centralizar em (-29.5, -56.0) com zoom 6
   - Deve mostrar Paraguai, Uruguai, Argentina
   - Timeline deve carregar frames F000, F003, F006, etc.
   - Header deve mostrar "ECMWF → CIM WRF 3 KM"

2. **Selecionar ICON → CIM 3 KM**
   - Mesmo comportamento acima
   - Header: "ICON → CIM WRF 3 KM"

3. **Alternar entre CIM e WRF Sul**
   - Bounds devem mudar corretamente
   - Não deixar cacheado o domínio anterior

4. **Verificar Refletividade**
   - Se disponível, deve usar paleta existente
   - `reflectivitySource` deve ser `REFL_10CM_NATIVE`

5. **PNG/GIF**
   - Exportação deve funcionar normalmente
   - Manter qualidade e paleta

---

## 12. Estrutura de URLs Esperada

O frontend buscará dados em:

```
https://raw.githubusercontent.com/SEU_USUARIO/sideral-meteorologia/cim-wrf3-ecmwf-data/metadata.json
https://raw.githubusercontent.com/SEU_USUARIO/sideral-meteorologia/cim-wrf3-ecmwf-data/f000.json.gz
https://raw.githubusercontent.com/SEU_USUARIO/sideral-meteorologia/cim-wrf3-ecmwf-data/f003.json.gz
...
```

E para ICON:
```
https://raw.githubusercontent.com/SEU_USUARIO/sideral-meteorologia/cim-wrf3-icon-data/metadata.json
...
```

---

## 13. Tratamento de Erros

Adicionar tratamento para quando dados não estiverem disponíveis:

```javascript
async function loadCIMData(modelKey) {
    try {
        const source = WRF_PUBLISHED_SOURCES[modelKey];
        const metadataUrl = `${source.root}${source.branch}/metadata.json`;
        
        const response = await fetch(metadataUrl);
        if (!response.ok) {
            throw new Error('Dados não disponíveis');
        }
        
        const metadata = await response.json();
        
        if (metadata.status !== 'complete') {
            showWarning('Rodada em processamento. Usando última disponível.');
            // Carregar última rodada válida
        }
        
        // Carregar frames...
    } catch (error) {
        showError('CIM WRF 3 KM indisponível no momento.');
        // Fallback para outro modelo ou mensagem
    }
}
```

---

## 14. Variáveis Exclusivas do WRF2

Se o frontend tem variáveis exclusivas do WRF 2 que o CIM ainda não publica:

```javascript
function isVariableAvailable(variable, modelKey) {
    const cimOnlyVariables = ['wrf2_exclusive_field'];
    
    if ((modelKey === 'ecmwf_cim_wrf3' || modelKey === 'icon_cim_wrf3') 
        && cimOnlyVariables.includes(variable)) {
        return false;
    }
    
    return true;
}
```

Mostrar mensagem clara: *"Variável X não disponível para CIM WRF 3 KM"*.

---

## Checklist Final

- [ ] Opções CIM adicionadas ao select
- [ ] Domínio `cim` definido em `MODEL_DOMAIN_BOUNDS`
- [ ] `domainKeyForModel()` retorna `'cim'` para ECMWF/ICON CIM
- [ ] `backendModelKey()` mapeia corretamente
- [ ] `WRF_PUBLISHED_SOURCES` configurado com branches corretas
- [ ] Modelos permitidos incluem `ecmwf_cim_wrf3` e `icon_cim_wrf3`
- [ ] Names/header atualizados
- [ ] Mapa centraliza automaticamente no domínio CIM
- [ ] Bounds do domínio são desenhados
- [ ] Alternância entre domínios funciona sem cache incorreto
- [ ] Tratamento de erros implementado
- [ ] Variáveis exclusivas tratadas corretamente

---

## Exemplo Completo de Alteração

```javascript
// ANTES (apenas sul e sudeste)
const MODEL_DOMAIN_BOUNDS = {
    'sul': { bounds: [...], label: 'WRF Sul 4km' },
    'sudeste': { bounds: [...], label: 'WRF Sudeste 4km' }
};

// DEPOIS (com CIM)
const MODEL_DOMAIN_BOUNDS = {
    'sul': { bounds: [...], label: 'WRF Sul 4km' },
    'sudeste': { bounds: [...], label: 'WRF Sudeste 4km' },
    'cim': {
        bounds: [[-40.0, -65.0], [-19.0, -47.0]],
        label: 'CIM · Sul / PY / UY / AR',
        center: [-29.5, -56.0],
        zoom: 6
    }
};

function domainKeyForModel(modelKey) {
    if (modelKey === 'ecmwf_cim_wrf3' || modelKey === 'icon_cim_wrf3') {
        return 'cim';  // NOVO
    }
    if (modelKey.includes('sudeste')) return 'sudeste';
    return 'sul';
}
```

---

**Próximos Passos**: Após integrar, testar com dados reais das branches `cim-wrf3-ecmwf-data` e `cim-wrf3-icon-data`.
