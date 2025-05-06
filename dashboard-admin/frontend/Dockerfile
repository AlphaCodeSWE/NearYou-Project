# dashboard-admin/frontend/Dockerfile
FROM node:20-alpine3.19

WORKDIR /app

# 1) Copia solo il package.json 
COPY package.json ./

# 2) Installa dipendenze 
RUN npm install --legacy-peer-deps

# 3) Copia il resto del sorgente
COPY . .

# 4) Costruisci la versione di produzione
RUN npm run build

# 5) Al container in produzione basta servire la build:
CMD ["npx", "serve", "-s", "build", "-l", "3000"]
