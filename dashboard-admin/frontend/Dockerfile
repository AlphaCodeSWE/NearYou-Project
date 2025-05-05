# dashboard-admin/frontend/Dockerfile

FROM node:18-alpine

# 2) cartella di lavoro
WORKDIR /app


COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

# 4) copia il resto del codice
COPY . .

# 5) esponi la porta del dev‐server React
EXPOSE 3000

# 6) comando di default: avvia il dev‐server
CMD ["yarn", "start"]
