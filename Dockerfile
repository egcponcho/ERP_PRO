# Compila la interfaz y la sirve desde el mismo contenedor que la API
FROM node:22-alpine AS web
WORKDIR /web
COPY frontend/package*.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ .
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
COPY --from=web /web/dist /frontend/dist
# Sin privilegios de administrador dentro del contenedor
RUN useradd --create-home --uid 1000 app && chown -R app /app
USER app
ENV PYTHONUNBUFFERED=1 FRONTEND_DIST=/frontend/dist
EXPOSE 8000
CMD ["sh", "./arrancar.sh"]
