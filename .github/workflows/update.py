import re
import json
from urllib import request


def get_website_source(url: str) -> str:
    return request.urlopen(url).read().decode('utf-8')


def get_aact_entry():
    source = get_website_source('https://aact.ctti-clinicaltrials.org/pipe_files')
    pattern = re.compile(r'(/static/exported_files/monthly/([0-9]{8})_pipe-delimited-export\.zip)')
    matches = pattern.findall(source)
    return {
        'version': matches[0][1][0:4] + '.' + matches[0][1][4:6] + '.' + matches[0][1][6:8] if len(
            matches) > 0 else None,
        'files': ['https://aact.ctti-clinicaltrials.org' + matches[0][0]] if len(matches) > 0 else []
    }


def get_drugcentral_entry():
    source = get_website_source('https://drugcentral.org/ActiveDownload')
    pattern = re.compile(
        r'(https://unmtid-shinyapps\.net/download/drugcentral\.dump\.([0-9]+)_([0-9]+)_([0-9]{4})\.sql\.gz)')
    matches = pattern.findall(source)
    return {
        'version': matches[0][3] + '.' + matches[0][1] + '.' + matches[0][2] if len(matches) > 0 else None,
        'files': [matches[0][0]] if len(matches) > 0 else []
    }


if __name__ == '__main__':
    result = {
        'AACT': get_aact_entry(),
        'DrugCentral': get_drugcentral_entry()
    }
    with open('../../result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=4, sort_keys=True)
