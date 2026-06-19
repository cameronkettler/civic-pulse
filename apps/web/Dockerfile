FROM node:22-alpine

WORKDIR /app

COPY apps/web/package*.json ./
RUN npm install

COPY apps/web ./

ENV NEXT_TELEMETRY_DISABLED=1
CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0"]
