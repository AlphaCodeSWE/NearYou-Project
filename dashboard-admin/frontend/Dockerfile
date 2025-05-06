# dashboard-admin/frontend/Dockerfile

FROM node:23-alpine3.19

WORKDIR /app

# 1) Copia solo package.json e package-lock.json per sfruttare la cache
COPY package.json package-lock.json ./

# 2) Installa le dipendenze in modo riproducibile
RUN npm ci

# 3) Copia il resto del codice
COPY . .

# 4) Costruisci la versione di produzione (in caso ne serva una)
RUN npm run build

# 5) Espone la porta React (normalmente 3000)
EXPOSE 3000

# 6) Avvia il dev-server
CMD ["npm", "start"]
