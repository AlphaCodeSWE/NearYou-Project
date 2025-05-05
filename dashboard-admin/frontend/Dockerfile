# dashboard-admin/frontend/Dockerfile
FROM node:18-alpine

# 1) Imposta la cartella di lavoro
WORKDIR /app

# 2) Copia solo package.json e installa
COPY package.json ./
RUN yarn install

# 3) Copia il resto del codice
COPY . .

EXPOSE 3000

# 5) Avvia in dev mode
CMD ["yarn", "start"]
