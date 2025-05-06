# dashboard-admin/frontend/Dockerfile

# 1) Base leggera con Node 20
FROM node:20-alpine3.19

# 2) Directory di lavoro
WORKDIR /app

# 3) Copia il package manifest e installa le dipendenze
COPY package.json ./
RUN npm install --legacy-peer-deps

# 4) Copia tutto il resto del sorgente
COPY . .

# 5) Espone la porta 3000 del dev-server
EXPOSE 3000

# 6) Avvia automaticamente il CRA dev-server
CMD ["npm", "start"]
