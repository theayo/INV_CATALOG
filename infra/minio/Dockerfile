FROM golang:1.24.8-alpine AS source
RUN apk add --no-cache git
ENV GOMAXPROCS=2

FROM source AS server-build
ARG MINIO_RELEASE=RELEASE.2025-10-15T17-29-55Z
WORKDIR /src
RUN git clone --depth 1 --branch "${MINIO_RELEASE}" https://github.com/minio/minio.git .
RUN CGO_ENABLED=0 go build -p 2 -trimpath -ldflags="-s -w" -o /out/minio .

FROM source AS client-build
ARG MC_RELEASE=RELEASE.2025-08-13T08-35-41Z
WORKDIR /src
RUN git clone --depth 1 --branch "${MC_RELEASE}" https://github.com/minio/mc.git .
RUN CGO_ENABLED=0 go build -p 2 -trimpath -ldflags="-s -w" -o /out/mc .

FROM alpine:3.23 AS runtime
RUN apk add --no-cache ca-certificates

FROM runtime AS client
COPY --from=client-build /out/mc /usr/local/bin/mc
COPY --from=client-build /src/LICENSE /licenses/minio-mc-AGPL-3.0.txt
ENTRYPOINT ["mc"]

FROM runtime AS server
COPY --from=server-build /out/minio /usr/local/bin/minio
COPY --from=server-build /src/LICENSE /licenses/minio-AGPL-3.0.txt
RUN mkdir -p /data
EXPOSE 9000 9001
ENTRYPOINT ["minio"]
CMD ["server", "/data", "--console-address", ":9001"]
