# dashboard-admin/frontend/Dockerfile

FROM node:20-alpine3.19

WORKDIR /app

# 1) Copia il manifest e (se presente) il lockfile
COPY package.json package-lock.json* ./

# 2) Installa le dipendenze e crea gli stub AJV
RUN npm install --legacy-peer-deps \
  && mkdir -p node_modules/ajv/dist/compile \
  && printf 'module.exports=require("./codegen");\n' > node_modules/ajv/dist/compile/context.js \
  && printf 'module.exports=function compile(){return {};}\n' > node_modules/ajv/dist/compile/codegen.js

# 3) Copia tutto il resto del frontend
COPY . .

# 4) Assicura i permessi di esecuzione (incluso eventuale fix script)
RUN chmod -R a+rx .

# 5) Espone la porta del dev‐server
EXPOSE 3000

# 6) Avvia automaticamente CRA
CMD ["npm", "start"]
