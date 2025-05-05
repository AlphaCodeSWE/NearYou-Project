# dashboard-admin/frontend/Dockerfile
FROM node:20-alpine3.19

WORKDIR /app

# 1) copia solo package.json (salta yarn.lock)
COPY package.json ./

# 2) installa dipendenze direttamente
RUN npm install --global yarn \
 && yarn install --non-interactive

# 3) copia il resto dei sorgenti
COPY . .

# 4) build
RUN yarn build

# 5) avvia in dev mode
ENV CI=true
CMD ["yarn", "start"]
