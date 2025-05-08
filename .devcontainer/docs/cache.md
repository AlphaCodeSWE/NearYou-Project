# Sistema di Cache per Messaggi LLM

## Introduzione

Questo documento descrive il sistema di cache implementato in NearYou per l'ottimizzazione delle chiamate ai servizi LLM (Large Language Model). L'obiettivo principale è migliorare le prestazioni della piattaforma, ridurre i costi operativi e aumentare la resilienza del sistema mantenendo la qualità delle risposte personalizzate.

## Architettura del Sistema

Il sistema di cache è strutturato come una componente modulare che si integra con il servizio di generazione messaggi esistente:

```
┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│                   │     │                   │     │                   │
│   Cache Service   │◄────┤ Message Generator ├────►│   LLM Provider    │
│   (Redis/Memory)  │     │     Service       │     │ (OpenAI/Groq/etc) │
│                   │     │                   │     │                   │
└───────────────────┘     └───────────────────┘     └───────────────────┘
```

### Componenti Principali:

1. **Modulo Redis**
   - `redis/redis_cache.py`: Implementazione client Redis con serializzazione JSON
   - `redis/memory_cache.py`: Implementazione in-memory per fallback e sviluppo

2. **Integrazione Message Generator**
   - `services/message_generator/cache_utils.py`: Utilities per generazione chiavi e gestione cache
   - `services/message_generator/app.py`: API con supporto cache integrato

3. **Container Redis**
   - Deployment tramite Docker Compose

## Strategie di Caching

Il sistema implementa diverse strategie avanzate per ottimizzare l'utilizzo della cache:

### 1. Fuzzy Matching

Le chiavi di cache sono generate con un sistema di "matching approssimativo" che permette il riutilizzo dei messaggi per richieste simili:

```python
def generate_cache_key(user_params, poi_params):
    # Normalizza età in intervalli (25-29, 30-34, etc.)
    age_range = f"{(age // 5) * 5}-{((age // 5) * 5) + 4}"
    
    # Normalizza interessi (ordine alfabetico)
    interests_list = sorted([i.strip().lower() for i in i.split(",")])
    
    # Crea hash MD5 dalla combinazione di parametri
    combined = f"{age_range}:{profession}:{interests}:{poi_name}:{category}"
    return hashlib.md5(combined.encode()).hexdigest()
```

Questo approccio permette di:
- Raggruppare utenti con età simile nella stessa cache
- Rendere insensibili all'ordine le liste di interessi
- Normalizzare case e spazi bianchi

### 2. TTL Adattivo

Il sistema varia automaticamente la durata di permanenza in cache (Time-To-Live) in base alla popolarità delle categorie:

```python
# Categorie popolari hanno TTL più lungo
if poi_category in popular_categories:
    ttl = CACHE_TTL * 2
```

### 3. Resilienza e Fallback

In caso di problemi con Redis, il sistema passa automaticamente a una cache in-memory:

```python
if cache.client is None:
    logger.warning("Redis non disponibile, usando cache in-memory")
    cache = MemoryCache(default_ttl=CACHE_TTL)
```

## Monitoraggio e Osservabilità

Il sistema include un endpoint dedicato per il monitoraggio delle prestazioni della cache:

```
GET /cache/stats
```

Risposta:
```json
{
  "enabled": true,
  "hits": 1250,
  "misses": 280,
  "total": 1530,
  "hit_rate": 0.8169,
  "cache_info": {
    "status": "connected",
    "used_memory_human": "2.5M",
    "connected_clients": 3,
    "uptime_in_days": 5.2,
    "hit_rate": 0.82
  }
}
```

## Configurazione

Il sistema è configurabile tramite variabili d'ambiente:

| Variabile | Descrizione | Default |
|-----------|-------------|---------|
| `CACHE_ENABLED` | Attiva/disattiva la cache | `true` |
| `CACHE_TTL` | Durata predefinita in secondi | `86400` (24h) |
| `REDIS_HOST` | Host del server Redis | `redis-cache` |
| `REDIS_PORT` | Porta Redis | `6379` |
| `REDIS_DB` | Database Redis | `0` |
| `REDIS_PASSWORD` | Password Redis | `""` |

## Benefici

L'implementazione di questo sistema di cache offre numerosi vantaggi:

1. **Riduzione Costi**
   - Riduzione fino all'80% delle chiamate API LLM
   - ROI significativo con provider a pagamento come OpenAI e Groq

2. **Miglioramento Prestazioni**
   - Latenza ridotta: ~1-5ms (cache) vs ~300-500ms (API LLM)
   - Esperienza utente più reattiva e fluida

3. **Maggiore Scalabilità**
   - Gestione efficiente dei picchi di carico
   - Riduzione del carico sui servizi esterni

4. **Disponibilità Migliorata**
   - Continuità del servizio durante interruzioni temporanee LLM
   - Strategie di fallback automatiche

## Esempio di Implementazione

Ecco come viene utilizzato il sistema nel flusso di generazione messaggi:

```python
@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    # Converti oggetti Pydantic in dict
    user_params = req.user.dict()
    poi_params = req.poi.dict()
    
    # Controlla cache
    cached_message = get_cached_message(user_params, poi_params)
    if cached_message:
        return GenerateResponse(message=cached_message, cached=True)
    
    # Se non in cache, genera nuovo messaggio
    prompt_text = template.format(...)
    result = call_llm(prompt_text)
    
    # Salva in cache
    cache_message(user_params, poi_params, result)
    
    return GenerateResponse(message=result, cached=False)
```

