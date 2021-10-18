import json


def get_drugcentral_entry():
    return {
        'version': None,
        'files': []
    }


if __name__ == '__main__':
    result = {
        'DrugCentral': get_drugcentral_entry()
    }
    with open('../../result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=4, sort_keys=True)
