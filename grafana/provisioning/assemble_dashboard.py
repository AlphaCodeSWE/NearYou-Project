#!/usr/bin/env python3
import json
import os
import re

def read_json_file(file_path):
    """Legge un file JSON e ritorna il suo contenuto."""
    with open(file_path, 'r') as f:
        return json.load(f)

def write_json_file(file_path, content):
    """Scrive il contenuto nel file JSON specificato."""
    with open(file_path, 'w') as f:
        json.dump(content, f, indent=2)

def main():
    # Percorsi corretti
    base_dir = "/workspace/NearYou-Project"
    panels_dir = os.path.join(base_dir, "grafana/provisioning/dashboards/panels")
    dashboard_template_path = os.path.join(base_dir, "grafana/provisioning/dashboards/near_you_dashboard.json")
    assembled_dashboard_path = os.path.join(base_dir, "grafana/provisioning/dashboards/near_you_dashboard_assembled.json")
    
    print(f"Leggendo template da: {dashboard_template_path}")
    print(f"Cartella pannelli: {panels_dir}")
    
    # Leggi il template della dashboard
    with open(dashboard_template_path, 'r') as f:
        dashboard_template = f.read()
    
    # Sostituisci i riferimenti ai pannelli
    panel_files = {
        "${PANEL_STAT_USERS}": "stat_users.json",
        "${PANEL_STAT_EVENTS}": "stat_event.json",  # Corretto qui - era stat_events.json
        "${PANEL_STAT_SHOPS}": "stat_shops.json",
        "${PANEL_CHART_EVENTS_PER_HOUR}": "chart_events_per_hour.json",
        "${PANEL_TOP_10_SHOPS}": "top_10_shops.json",
        "${PANEL_MAP_USER_ROUTES}": "map_user_routes.json",
        "${PANEL_MAP_SHOPS}": "map_shops.json"
    }
    
    panels = []
    for placeholder, filename in panel_files.items():
        file_path = os.path.join(panels_dir, filename)
        print(f"Leggendo pannello da: {file_path}")
        try:
            panel_content = read_json_file(file_path)
            panels.append(panel_content)
        except Exception as e:
            print(f"Errore durante la lettura di {file_path}: {e}")
        
    # Sostituisci la lista dei pannelli
    dashboard_template = re.sub(
        r'"panels":\s*\[(.*?)\]', 
        f'"panels": {json.dumps(panels, indent=2)}', 
        dashboard_template,
        flags=re.DOTALL
    )
    
    # Assembla e aggiungi le variabili di template
    template_variables = []
    
    # Aggiungi le variabili di filtro principali
    try:
        template_variables.append(read_json_file(os.path.join(panels_dir, "template_age.json")))
        template_variables.append(read_json_file(os.path.join(panels_dir, "template_profession.json")))
        template_variables.append(read_json_file(os.path.join(panels_dir, "template_interests.json")))
        
        # Aggiungi le variabili di filtro SQL
        for filter_var in read_json_file(os.path.join(panels_dir, "template_filters.json")):
            template_variables.append(filter_var)
        
        # Aggiungi le costanti per le datasource
        for ds in read_json_file(os.path.join(panels_dir, "template_datasources.json")):
            template_variables.append(ds)
    except Exception as e:
        print(f"Errore durante l'assemblaggio delle variabili template: {e}")
    
    # Sostituisci la lista delle variabili di template
    dashboard_template = re.sub(
        r'"templating":\s*\{\s*"list":\s*\${TEMPLATE_VARIABLES}\s*\}', 
        f'"templating": {{\n    "list": {json.dumps(template_variables, indent=2)}\n  }}', 
        dashboard_template,
        flags=re.DOTALL
    )
    
    # Salva la dashboard assemblata
    with open(assembled_dashboard_path, 'w') as f:
        f.write(dashboard_template)
    
    print(f"Dashboard assemblata con successo in: {assembled_dashboard_path}")

if __name__ == "__main__":
    main()