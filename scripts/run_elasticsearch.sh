#!/bin/bash
set -e

docker run -d \
  --name elasticsearch-dev \
  -e discovery.type=single-node \
  -e ES_JAVA_OPTS="-Xms512m -Xmx512m" \
  -e ELASTIC_PASSWORD=elastic \
  -e xpack.security.enabled=true \
  -e xpack.security.transport.ssl.enabled=false \
  -e xpack.security.http.ssl.enabled=false \
  -e bootstrap.memory_lock=true \
  -e TZ=UTC \
  -p 9200:9200 \
  docker.elastic.co/elasticsearch/elasticsearch:9.0.3
