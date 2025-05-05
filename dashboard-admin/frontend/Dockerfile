FROM node:20-alpine3.19

WORKDIR /app

# 1) Copia file di definizione delle dipendenze
COPY package.json yarn.lock ./

# 2) Installa yarn
RUN npm install -g yarn

# 3) Installa le dipendenze
RUN yarn install --frozen-lockfile --non-interactive

# 4) Copia tutto il resto dei sorgenti
COPY . .

RUN yarn build

ENV CI=true
CMD ["yarn", "start"]
