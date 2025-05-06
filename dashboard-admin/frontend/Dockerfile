# dashboard-admin/frontend/Dockerfile

# 1) Usa Alpine + Node 20
FROM node:20-alpine3.19

# 2) Imposta la working dir
WORKDIR /app

# 3) Copia solo file di lock e package per sfruttare la cache di Docker
COPY package.json package-lock.json ./

# 4) Installa le dipendenze (legacy-peer-deps per evitare conflitti con react-scripts)
RUN npm install --legacy-peer-deps

# 5) Copia tutto il sorgente
COPY . .

# 6) Espone la porta 3000 per il dev server CRA
EXPOSE 3000

# 7) Comando di default: avvia il dev-server
CMD ["npm", "start"]
