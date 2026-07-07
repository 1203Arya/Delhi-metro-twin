FROM node:24-alpine AS builder
WORKDIR /build

COPY web/package.json web/package-lock.json ./
RUN npm ci

COPY web/ .
RUN npm run build

FROM node:24-alpine AS runner
RUN addgroup -S dmdt && adduser -S dmdt dmdt
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

COPY --from=builder /build/public ./public
COPY --from=builder /build/.next/standalone ./
COPY --from=builder /build/.next/static ./.next/static

EXPOSE 3000
USER dmdt

CMD ["node", "server.js"]
