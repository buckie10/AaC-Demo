#!/bin/sh
set -eu
base=http://fuseki:3030/architecture/data?default
for file in /semantic/ontology.ttl /semantic/canonical_world.ttl; do
  curl -fsS -X POST "$base" -H 'Content-Type: text/turtle' --data-binary "@$file"
done
echo 'Fuseki bootstrap complete'
