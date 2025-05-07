-- "Visite per Negozio" con tutti i filtri applicati
SELECT 
    poi_name,
    toStartOfHour(event_time) as time,
    COUNT(*) as visits
FROM nearyou.user_events e
JOIN nearyou.users u ON e.user_id = u.user_id
WHERE 
    -- Filtro temporale
    event_time >= NOW() - INTERVAL ${time_range:raw}
    
    -- Filtro fascia oraria
    AND (
        '$__all' IN ('${day_time:raw}')
        OR (toHour(event_time) >= 6 AND toHour(event_time) < 12 AND 'morning' IN ('${day_time:raw}'))
        OR (toHour(event_time) >= 12 AND toHour(event_time) < 18 AND 'afternoon' IN ('${day_time:raw}'))
        OR (toHour(event_time) >= 18 AND toHour(event_time) < 24 AND 'evening' IN ('${day_time:raw}'))
        OR (toHour(event_time) >= 0 AND toHour(event_time) < 6 AND 'night' IN ('${day_time:raw}'))
    )
    
    -- Filtro fascia d'età
    AND (
        '$__all' IN ('${age_range:raw}')
        OR u.age IN (${age_range:csv})
    )
    
    -- Filtro professione
    AND (
        '$__all' IN ('${profession:raw}')
        OR u.profession IN (${profession:csv})
    )
    
    -- Filtro popolarità negozio
    AND (
        '$__all' IN ('${shop_popularity:raw}')
        OR (
            -- Questa parte richiede una subquery o una vista materializzata in un caso reale
            -- Per semplicità, qui utilizziamo una condizione approssimativa
            ('high' IN ('${shop_popularity:raw}') AND poi_name IN (
                SELECT poi_name FROM nearyou.user_events
                GROUP BY poi_name HAVING COUNT(*) > 100
            ))
            OR ('medium' IN ('${shop_popularity:raw}') AND poi_name IN (
                SELECT poi_name FROM nearyou.user_events
                GROUP BY poi_name HAVING COUNT(*) BETWEEN 20 AND 100
            ))
            OR ('low' IN ('${shop_popularity:raw}') AND poi_name IN (
                SELECT poi_name FROM nearyou.user_events
                GROUP BY poi_name HAVING COUNT(*) < 20
            ))
        )
    )
    
GROUP BY poi_name, time
ORDER BY time DESC, visits DESC
LIMIT 100