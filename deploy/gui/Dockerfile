FROM node:20

WORKDIR /usr/src/app

COPY package*.json ./
RUN npm i

COPY src/app/ .

EXPOSE 5173

CMD ["sh", "-c", "npm i && npm run dev"]
