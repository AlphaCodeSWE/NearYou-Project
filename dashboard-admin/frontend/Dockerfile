# dashboard-admin/frontend/Dockerfile
FROM node:16-alpine

WORKDIR /app

# 1) Copia solo i file di dipendenze e configurazione TS
COPY package.json yarn.lock tsconfig.json ./

# 2) Installa le dipendenze 
RUN yarn install --frozen-lockfile

# 3) Copia tutto il resto del frontend
COPY . .


RUN yarn build

# 5) Porta in ascolto e comando di avvio dev
ENV CI=true
EXPOSE 3000
CMD ["yarn", "start"]
