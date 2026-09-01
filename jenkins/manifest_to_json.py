import json
import sys
import yaml


with open(sys.argv[1], encoding="utf-8") as source:
    print(json.dumps(yaml.safe_load(source), sort_keys=True))
