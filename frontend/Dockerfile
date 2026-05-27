FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 5173

# Bind to 0.0.0.0 to make it accessible outside the container
CMD ["npm", "run", "dev", "--", "--host"]
