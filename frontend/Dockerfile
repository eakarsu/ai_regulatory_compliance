FROM node:20-bookworm-slim AS build
WORKDIR /app
ARG VITE_API_BASE=/api
ENV VITE_API_BASE=$VITE_API_BASE
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginxinc/nginx-unprivileged:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
