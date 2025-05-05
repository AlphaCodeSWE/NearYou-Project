# dashboard-admin/frontend/Dockerfile

# 1) Prendiamo Node 23-alpine3.19 esattamente al digest verificato
ARG NODE_VERSION=23-alpine3.19@sha256:21cb32fcd4012de64c546bc0d5cbde405362f6c3d515ba81d04ebbcd373daa9e
FROM node:${NODE_VERSION}

WORKDIR /app

# 2) Per debug, vediamo subito le versioni
RUN node --version && yarn --version

# 3) Copia solo il manifest delle dipendenze
COPY package.json tsconfig.json ./

# 4) Installa le dipendenze
#    - se c'è yarn.lock, lo rispetta; altrimenti ne genera uno nuovo
RUN yarn install --frozen-lockfile --non-interactive || yarn install --non-interactive

# 5) Copia tutto il resto del sorgente
COPY . .


RUN yarn build

# 7) Espone la porta che userai in docker-compose e lancia in dev
EXPOSE 3000
CMD ["yarn", "start"]
