# dashboard-admin/frontend/Dockerfile
FROM node:16-alpine

WORKDIR /app

# 1) Copia solo package.json 
COPY package.json tsconfig.json ./


RUN yarn install

# 3) Copia il resto del codice
COPY . .


# RUN yarn build

# 5) Espone la porta 3000 e avvia la app in dev mode
EXPOSE 3000
CMD ["yarn", "start"]
