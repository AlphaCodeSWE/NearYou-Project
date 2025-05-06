# dashboard-admin/frontend/Dockerfile

FROM node:20-alpine3.19

WORKDIR /app

# 1) Copia il package.json e lo script di fix
COPY package.json fix-ajv.js ./

# 2) Installa le dipendenze (e scatta il postinstall che esegue fix-ajv.js)
RUN npm install --legacy-peer-deps

# 3) Copia tutto il resto del sorgente
COPY . .

# 4) Espone la porta del dev-server CRA
EXPOSE 3000

# 5) Avvia automaticamente il dev-server
CMD ["npm", "start"]
