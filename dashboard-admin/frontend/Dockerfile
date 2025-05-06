# usa Alpine + Node 20 (ultimo tag senza vulnerabilità critiche)
FROM node:20-alpine3.19

WORKDIR /app

# 1) copia package.json e installa subito le dipendenze
COPY package.json ./
# bypass peer-deps inconciliabili con react-scripts@5
RUN npm install --legacy-peer-deps

# 2) copia tutto il sorgente
COPY . .

# 3) build della versione di produzione
RUN npm run build

# 4) espone la porta del dev-server
EXPOSE 3000

# 5) di default lancia il server React in dev-mode
CMD ["npm", "start"]
