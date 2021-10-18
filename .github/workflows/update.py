import re
import json
from urllib import request


def get_drugcentral_entry():
    source = request.urlopen('https://drugcentral.org/ActiveDownload').read().decode('utf-8')
    pattern = re.compile(
        '(https://unmtid-shinyapps\\.net/download/drugcentral\\.dump\\.([0-9]+)_([0-9]+)_([0-9]{4})\\.sql\\.gz)')
    matches = pattern.findall(source)
    return {
        'version': matches[0][1] + '.' + matches[0][2] + '.' + matches[0][3] if len(matches) > 0 else None,
        'files': [matches[0][0]] if len(matches) > 0 else []
    }


if __name__ == '__main__':
    result = {
        'DrugCentral': get_drugcentral_entry()
    }
    with open('../../result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=4, sort_keys=True)
