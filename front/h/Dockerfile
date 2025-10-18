
FROM node:20-alpine

# Ensure glibc compatibility for some Node packages/binaries
RUN apk add --no-cache libc6-compat

WORKDIR /app


ENV CHOKIDAR_USEPOLLING=true \
    WATCHPACK_POLLING=true

COPY package*.json ./
RUN npm ci --no-audit --no-fund


COPY . .


EXPOSE 5175
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5175"]
