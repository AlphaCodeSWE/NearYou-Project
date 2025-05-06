# dashboard-admin/frontend/Dockerfile

FROM node:20-alpine3.19
WORKDIR /app

# 1) Copia solo package.json + fix script
COPY package.json fix-ajv.js ./

# 2) Rendi eseguibile e installa le dipendenze (con postinstall che crea gli stub)
RUN chmod +x fix-ajv.js \
    && npm install --legacy-peer-deps

# 3) Copia il resto del sorgente
COPY . .

# 4) Espone la porta del dev-server CRA
EXPOSE 3000

# 5) Avvia automaticamente il dev-server
CMD ["npm", "start"]
