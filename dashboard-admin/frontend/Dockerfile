# Usa una LTS moderna senza vulnerabilità critiche
FROM node:20-alpine3.19

WORKDIR /app

# 1) Copia solo package.json per installare dipendenze
COPY package.json ./

# 2) Installa con npm 
RUN npm install

# 3) Copia tutto il resto del sorgente
COPY . .

# 4) Build dell’app React
RUN npm run build

# 5) Avvio in dev
ENV CI=true
CMD ["npm", "start"]
