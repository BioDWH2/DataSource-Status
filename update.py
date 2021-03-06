import re
import json
import requests
from ftplib import FTP
from io import BytesIO
from zipfile import ZipFile
from datetime import datetime
from dateutil import parser
from typing import Dict, Union, List

try:
    from typing_extensions import TypedDict
except ModuleNotFoundError:
    pass


class Entry(TypedDict):
    version: Union[str, None]
    files: Dict[str, Union[str, None]]
    latest: bool


DEFAULT: List[Entry] = []

MONTHS_SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def get_website_source(url: str) -> str:
    headers = {'User-Agent': 'DataSource-Status Fetcher'}
    return requests.get(url, headers=headers).content.decode('utf-8')


def get_obo_ontology_version_line(url: str) -> Union[str, None]:
    r = requests.get(url, stream=True)
    for line in r.iter_lines():
        if line.decode('utf-8').strip().startswith("data-version:"):
            return line.decode('utf-8')
    return None


def get_aact_entry() -> List[Entry]:
    source = get_website_source('https://aact.ctti-clinicaltrials.org/pipe_files')
    pattern = re.compile(r'(/static/exported_files/monthly/([0-9]{8})_pipe-delimited-export\.zip)')
    matches = pattern.findall(source)
    entry: Entry = {
        'version': matches[0][1][0:4] + '.' + matches[0][1][4:6] + '.' + matches[0][1][6:8],
        'files': {
            'pipe-delimited-export.zip': 'https://aact.ctti-clinicaltrials.org' + matches[0][0]
        },
        'latest': True
    }
    return [entry]


def get_canadian_nutrient_file_entry() -> List[Entry]:
    source = get_website_source('https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/' +
                                'nutrient-data/canadian-nutrient-file-2015-download-files.html')
    pattern = re.compile(r'dateModified">\s*([0-9]{4})-([0-9]{2})-([0-9]{2})\s*</time>')
    matches = pattern.findall(source)
    entry: Entry = {
        'version': matches[0][0] + '.' + matches[0][1] + '.' + matches[0][2],
        'files': {
            'cnf-fcen-csv.zip': 'https://www.canada.ca/content/dam/hc-sc/migration/hc-sc/fn-an/alt_formats/zip/' +
                                'nutrition/fiche-nutri-data/cnf-fcen-csv.zip'
        },
        'latest': True
    }
    return [entry]


def get_cancer_drugs_db_entry() -> List[Entry]:
    source = get_website_source('https://www.anticancerfund.org/en/cancerdrugs-db')
    pattern = re.compile(r'Database build date:\s+([0-9]{2})/([0-9]{2})/([0-9]{2})', re.IGNORECASE)
    matches = pattern.findall(source)
    entry: Entry = {
        'version': matches[0][2] + '.' + matches[0][1] + '.' + matches[0][0],
        'files': {
            'cancerdrugsdb.txt': 'https://acfdata.coworks.be/cancerdrugsdb.txt'
        },
        'latest': True
    }
    return [entry]


def get_dgidb_entry() -> List[Entry]:
    # TODO
    return DEFAULT


def get_drugbank_entry() -> List[Entry]:
    releases = json.loads(get_website_source('http://go.drugbank.com/releases.json'))
    latest_version = sorted([release['version'] for release in releases], reverse=True)[0]
    versions = []
    for release in releases:
        url = release['url']
        entry: Entry = {
            'version': release['version'],
            'files': {
                'drugbank_all_full_database.xml.zip': url + '/downloads/all-full-database',
                'drugbank_all_structures.sdf.zip': url + '/downloads/all-structures',
                'drugbank_all_metabolite-structures.sdf.zip': url + '/downloads/all-metabolite-structures',
            },
            'latest': release['version'] == latest_version
        }
        versions.append(entry)
    return versions


def get_drugcentral_entry() -> List[Entry]:
    source = get_website_source('https://drugcentral.org/ActiveDownload')
    pattern = re.compile(
        r'(https://unmtid-shinyapps\.net/download/drugcentral\.dump\.([0-9]+)_([0-9]+)_([0-9]{4})\.sql\.gz)')
    matches = pattern.findall(source)
    entry: Entry = {
        'version': matches[0][3] + '.' + matches[0][1] + '.' + matches[0][2],
        'files': {
            'drugcentral.dump.sql.gz': matches[0][0]
        },
        'latest': True
    }
    return [entry]


def get_ema_entry() -> List[Entry]:
    # EMA updates the medicine data tables once a day
    entry: Entry = {
        'version': datetime.today().strftime('%Y.%m.%d'),
        'files': {
            'Medicines_output_european_public_assessment_reports.xlsx':
                'https://www.ema.europa.eu/sites/default/files/' +
                'Medicines_output_european_public_assessment_reports.xlsx',
            'Medicines_output_herbal_medicines.xlsx':
                'https://www.ema.europa.eu/sites/default/files/Medicines_output_herbal_medicines.xlsx'
        },
        'latest': True
    }
    return [entry]


def get_gene2phenotype_entry() -> List[Entry]:
    source = get_website_source('https://www.ebi.ac.uk/gene2phenotype')
    pattern = re.compile(r'<strong>([0-9]{4})-([0-9]{2})-([0-9]{2})</strong>')
    matches = pattern.findall(source)
    entry: Entry = {
        'version': matches[0][0] + '.' + matches[0][1] + '.' + matches[0][2],
        'files': {
            'CancerG2P.csv.gz': 'https://www.ebi.ac.uk/gene2phenotype/downloads/CancerG2P.csv.gz',
            'DDG2P.csv.gz': 'https://www.ebi.ac.uk/gene2phenotype/downloads/DDG2P.csv.gz',
            'EyeG2P.csv.gz': 'https://www.ebi.ac.uk/gene2phenotype/downloads/EyeG2P.csv.gz',
            'SkinG2P.csv.gz': 'https://www.ebi.ac.uk/gene2phenotype/downloads/SkinG2P.csv.gz'
        },
        'latest': True
    }
    return [entry]


def get_gene_ontology_entry() -> List[Entry]:
    obo_url = 'http://current.geneontology.org/ontology/go.obo'
    version_line = get_obo_ontology_version_line(obo_url)
    pattern = re.compile(r'([0-9]{4})-([0-9]{2})-([0-9]{2})')
    matches = pattern.findall(version_line)
    entry: Entry = {
        'version': matches[0][0] + '.' + matches[0][1] + '.' + matches[0][2],
        'files': {
            'go.obo': obo_url,
            'goa_human.gaf.gz': 'http://current.geneontology.org/annotations/goa_human.gaf.gz',
            'goa_human_complex.gaf.gz': 'http://current.geneontology.org/annotations/goa_human_complex.gaf.gz',
            'goa_human_isoform.gaf.gz': 'http://current.geneontology.org/annotations/goa_human_isoform.gaf.gz',
            'goa_human_rna.gaf.gz': 'http://current.geneontology.org/annotations/goa_human_rna.gaf.gz'
        },
        'latest': True
    }
    return [entry]


def get_gwas_catalog_entry() -> List[Entry]:
    headers = {'User-Agent': 'DataSource-Status Fetcher'}
    request = requests.get('https://www.ebi.ac.uk/gwas/api/search/downloads/alternative', headers=headers, stream=True)
    disposition = request.headers['content-disposition']
    file_name = re.findall("filename=(.+)", disposition)[0].strip()
    pattern = re.compile('([0-9]{4})-([0-9]{2})-([0-9]{2})')
    matches = pattern.findall(file_name)
    entry: Entry = {
        'version': matches[0][0] + '.' + matches[0][1] + '.' + matches[0][2],
        'files': {
            'gwas_catalog_associations.tsv': 'https://www.ebi.ac.uk/gwas/api/search/downloads/alternative',
            'gwas_catalog_studies.tsv': 'https://www.ebi.ac.uk/gwas/api/search/downloads/studies_alternative',
            'gwas_catalog_ancestry.tsv': 'https://www.ebi.ac.uk/gwas/api/search/downloads/ancestry'
        },
        'latest': True
    }
    return [entry]


def get_hgnc_entry() -> List[Entry]:
    ftp = FTP('ftp.ebi.ac.uk')
    ftp.login()
    modified_datetime = parser.parse(
        ftp.voidcmd('MDTM pub/databases/genenames/new/tsv/hgnc_complete_set.txt')[4:].strip())
    ftp.close()
    entry: Entry = {
        'version': modified_datetime.strftime('%Y.%m.%d'),
        'files': {
            'hgnc_complete_set.txt': 'https://ftp.ebi.ac.uk/pub/databases/genenames/new/tsv/hgnc_complete_set.txt'
        },
        'latest': True
    }
    return [entry]


def get_hpo_entry() -> List[Entry]:
    obo_url = 'https://raw.githubusercontent.com/obophenotype/human-phenotype-ontology/master/hp.obo'
    version_line = get_obo_ontology_version_line(obo_url)
    pattern = re.compile(r'([0-9]{4})-([0-9]{2})-([0-9]{2})')
    matches = pattern.findall(version_line)
    entry: Entry = {
        'version': matches[0][0] + '.' + matches[0][1] + '.' + matches[0][2],
        'files': {
            'hp.obo': obo_url,
            'phenotype.hpoa': 'http://purl.obolibrary.org/obo/hp/hpoa/phenotype.hpoa',
            'genes_to_phenotype.txt': 'http://purl.obolibrary.org/obo/hp/hpoa/genes_to_phenotype.txt',
            'phenotype_to_genes.txt': 'http://purl.obolibrary.org/obo/hp/hpoa/phenotype_to_genes.txt'
        },
        'latest': True
    }
    return [entry]


def get_itis_entry() -> List[Entry]:
    source = get_website_source('https://www.itis.gov/downloads/index.html')
    pattern = re.compile(
        r'files are currently from the <b>([0-9]{2})-(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-([0-9]{4})</b>')
    matches = pattern.findall(source)
    entry: Entry = {
        'version': matches[0][2] + '.' + str(MONTHS_SHORT.index(matches[0][1]) + 1) + '.' + matches[0][0],
        'files': {
            'itisMySQLTables.tar.gz': 'https://www.itis.gov/downloads/itisMySQLTables.tar.gz'
        },
        'latest': True
    }
    return [entry]


def get_kegg_entry() -> List[Entry]:
    ftp = FTP('ftp.genome.jp')
    ftp.login()
    modified_datetimes = [parser.parse(ftp.voidcmd('MDTM pub/kegg/medicus/' + x)[4:].strip()) for x in
                          ['dgroup/dgroup', 'disease/disease', 'drug/drug', 'network/network']]
    ftp.close()
    version = sorted([x.strftime('%Y.%m.%d') for x in modified_datetimes], reverse=True)[0]
    entry: Entry = {
        'version': version,
        'files': {
            'dgroup': 'ftp://ftp.genome.jp/pub/kegg/medicus/dgroup/dgroup',
            'drug': 'ftp://ftp.genome.jp/pub/kegg/medicus/drug/drug',
            'disease': 'ftp://ftp.genome.jp/pub/kegg/medicus/disease/disease',
            'network': 'ftp://ftp.genome.jp/pub/kegg/medicus/network/network',
            'variant': 'ftp://ftp.genome.jp/pub/kegg/medicus/network/variant',
            'human_genes_list.tsv': 'http://rest.kegg.jp/list/hsa',
            'compounds_list.tsv': 'http://rest.kegg.jp/list/compound',
            'organisms_list.tsv': 'http://rest.kegg.jp/list/organism',
        },
        'latest': True
    }
    return [entry]


def get_med_rt_entry() -> List[Entry]:
    ftp = FTP('ftp1.nci.nih.gov')
    ftp.login()
    file_paths = ftp.nlst('/pub/cacore/EVS/MED-RT/Archive')
    file_names = [x.split('/')[-1] for x in file_paths if
                  x.split('/')[-1].startswith('Core_MEDRT_') and x.split('/')[-1].endswith('_XML.zip')]
    file_names = sorted(file_names, reverse=True)
    ftp.close()
    pattern = re.compile(r'([0-9]{4}\.[0-9]{2}\.[0-9]{2})')
    versions = []
    for file_name in file_names:
        matches = pattern.findall(file_name)
        entry: Entry = {
            'version': matches[0],
            'files': {
                'Core_MEDRT_XML.zip': 'https://evs.nci.nih.gov/ftp1/MED-RT/Archive/' + file_name
            },
            'latest': file_name == file_names[0]
        }
        versions.append(entry)
    return versions


def get_mondo_entry() -> List[Entry]:
    obo_url = 'http://purl.obolibrary.org/obo/mondo.obo'
    version_line = get_obo_ontology_version_line(obo_url)
    pattern = re.compile(r'([0-9]{4})-([0-9]{2})-([0-9]{2})')
    matches = pattern.findall(version_line)
    entry: Entry = {
        'version': matches[0][0] + '.' + matches[0][1] + '.' + matches[0][2],
        'files': {
            'mondo.obo': obo_url
        },
        'latest': True
    }
    return [entry]


def get_ndf_rt_entry() -> List[Entry]:
    ftp = FTP('ftp1.nci.nih.gov')
    ftp.login()
    file_paths = ftp.nlst('/pub/cacore/EVS/NDF-RT/Archive')
    file_names = [x.split('/')[-1] for x in file_paths if x.split('/')[-1].startswith('NDFRT_Public_All')]
    file_names = sorted(file_names, reverse=True)
    ftp.close()
    pattern = re.compile(r'([0-9]{4})-([0-9]{2})-([0-9]{2})')
    versions = []
    for file_name in file_names:
        matches = pattern.findall(file_name)
        entry: Entry = {
            'version': matches[0][0] + '.' + matches[0][1] + '.' + matches[0][2],
            'files': {
                'NDFRT_Public_All.zip': 'https://evs.nci.nih.gov/ftp1/NDF-RT/Archive/' + file_name
            },
            'latest': file_name == file_names[0]
        }
        versions.append(entry)
    return versions


def get_open_targets_entry() -> List[Entry]:
    # TODO
    return DEFAULT


def get_pathway_commons_entry() -> List[Entry]:
    version_source = get_website_source('https://www.pathwaycommons.org/archives/PC2/')
    version_pattern = re.compile(r'<a href="v([0-9]+)/">v([0-9]+)/</a>')
    matches = sorted([int(x[0]) for x in version_pattern.findall(version_source)], reverse=True)
    versions = []
    for version in matches:
        if version < 9:
            break
        url_prefix = 'https://www.pathwaycommons.org/archives/PC2/v%s/' % version
        entry: Entry = {
            'version': str(version),
            'files': {
                'pathways.txt.gz': url_prefix + 'pathways.txt.gz',
                'datasources.txt': url_prefix + 'datasources.txt',
                'PathwayCommons.All.uniprot.gmt.gz': url_prefix + 'PathwayCommons%s.All.uniprot.gmt.gz' % version,
                'PathwayCommons.All.hgnc.txt.gz': url_prefix + 'PathwayCommons%s.All.hgnc.txt.gz' % version,
                'PathwayCommons.All.hgnc.sif.gz': url_prefix + 'PathwayCommons%s.All.hgnc.sif.gz' % version,
                'PathwayCommons.All.hgnc.gmt.gz': url_prefix + 'PathwayCommons%s.All.hgnc.gmt.gz' % version,
                'PathwayCommons.All.BIOPAX.owl.gz': url_prefix + 'PathwayCommons%s.All.BIOPAX.owl.gz' % version,
            },
            'latest': version == matches[0]
        }
        versions.append(entry)
    return versions


def get_pharmgkb_entry() -> List[Entry]:
    pattern = re.compile(r'([0-9]{4})-([0-9]{2})-([0-9]{2})')
    version = None
    r = requests.get('https://s3.pgkb.org/data/drugLabels.zip', stream=True)
    with ZipFile(BytesIO(r.content)) as zip_file:
        for item in zip_file.filelist:
            if item.filename.startswith('CREATED'):
                match = pattern.findall(item.filename)[0]
                version = match[0] + '.' + match[1] + '.' + match[2]
                break
    entry: Entry = {
        'version': version,
        'files': {
            'genes.zip': 'https://s3.pgkb.org/data/genes.zip',
            'drugs.zip': 'https://s3.pgkb.org/data/drugs.zip',
            'chemicals.zip': 'https://s3.pgkb.org/data/chemicals.zip',
            'variants.zip': 'https://s3.pgkb.org/data/variants.zip',
            'phenotypes.zip': 'https://s3.pgkb.org/data/phenotypes.zip',
            'clinicalAnnotations.zip': 'https://s3.pgkb.org/data/clinicalAnnotations.zip',
            'variantAnnotations.zip': 'https://s3.pgkb.org/data/variantAnnotations.zip',
            'relationships.zip': 'https://s3.pgkb.org/data/relationships.zip',
            'dosingGuidelines.json.zip': 'https://s3.pgkb.org/data/dosingGuidelines.json.zip',
            'drugLabels.zip': 'https://s3.pgkb.org/data/drugLabels.zip',
            'pathways-tsv.zip': 'https://s3.pgkb.org/data/pathways-tsv.zip',
            'clinicalVariants.zip': 'https://s3.pgkb.org/data/clinicalVariants.zip',
            'occurrences.zip': 'https://s3.pgkb.org/data/occurrences.zip',
            'automated_annotations.zip': 'https://s3.pgkb.org/data/automated_annotations.zip'
        },
        'latest': True
    }
    return [entry]


def get_redo_db_entry() -> List[Entry]:
    source = get_website_source('https://www.anticancerfund.org/en/redo-db')
    pattern = re.compile(r'Database build date:\s+([0-9]{2})/([0-9]{2})/([0-9]{2})', re.IGNORECASE)
    matches = pattern.findall(source)
    entry: Entry = {
        'version': matches[0][2] + '.' + matches[0][1] + '.' + matches[0][0],
        'files': {
            'redo_db.txt': 'https://acfdata.coworks.be/redo_db.txt'
        },
        'latest': True
    }
    return [entry]


def get_redo_trials_db_entry() -> List[Entry]:
    source = get_website_source('https://www.anticancerfund.org/en/redo-trials-db')
    pattern = re.compile(r'<span id=\'Last_Import\'>\s*([0-9]{2})/([0-9]{2})/([0-9]{4})', re.IGNORECASE)
    matches = pattern.findall(source)
    entry: Entry = {
        'version': matches[0][2] + '.' + matches[0][1] + '.' + matches[0][0],
        'files': {
            'ReDO_Trials_DB.txt': 'https://acfdata.coworks.be/ReDO_Trials_DB.txt'
        },
        'latest': True
    }
    return [entry]


def get_sider_entry() -> List[Entry]:
    ftp = FTP('xi.embl.de')
    ftp.login()
    modified_datetime = parser.parse(ftp.voidcmd('MDTM /SIDER/latest/meddra_all_label_se.tsv.gz')[4:].strip())
    ftp.close()
    entry: Entry = {
        'version': modified_datetime.strftime('%Y.%m.%d'),
        'files': {
            'drug_names.tsv': 'http://sideeffects.embl.de/media/download/drug_names.tsv',
            'drug_atc.tsv': 'http://sideeffects.embl.de/media/download/drug_atc.tsv',
            'meddra_all_label_indications.tsv.gz': 'ftp://xi.embl.de/SIDER/latest/meddra_all_label_indications.tsv.gz',
            'meddra_all_label_se.tsv.gz': 'ftp://xi.embl.de/SIDER/latest/meddra_all_label_se.tsv.gz',
            'meddra_freq.tsv.gz': 'ftp://xi.embl.de/SIDER/latest/meddra_freq.tsv.gz',
        },
        'latest': True
    }
    return [entry]


def get_unii_entry() -> List[Entry]:
    source = get_website_source('https://fdasis.nlm.nih.gov/srs/jsp/srs/uniiListDownload.jsp')
    pattern = re.compile(r'Last updated: (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) ([0-9]{4})')
    matches = pattern.findall(source)
    entry: Entry = {
        'version': matches[0][1] + '.' + str(MONTHS_SHORT.index(matches[0][0]) + 1),
        'files': {
            'UNIIs.zip': 'https://fdasis.nlm.nih.gov/srs/download/srs/UNIIs.zip',
            'UNII_Data.zip': 'https://fdasis.nlm.nih.gov/srs/download/srs/UNII_Data.zip'
        },
        'latest': True
    }
    return [entry]


def get_uniprot_entry() -> List[Entry]:
    ftp = FTP('ftp.uniprot.org')
    ftp.login()
    modified_datetime = parser.parse(ftp.voidcmd(
        'MDTM pub/databases/uniprot/current_release/knowledgebase/taxonomic_divisions/uniprot_sprot_human.xml.gz')[
                                     4:].strip())
    ftp.close()
    entry: Entry = {
        'version': modified_datetime.strftime('%Y.%m.%d'),
        'files': {
            'uniprot_sprot_human.xml.gz': 'https://ftp.uniprot.org/pub/databases/uniprot/current_release/' +
                                          'knowledgebase/taxonomic_divisions/uniprot_sprot_human.xml.gz'
        },
        'latest': True
    }
    return [entry]


def get_usda_plants_entry() -> List[Entry]:
    entry: Entry = {
        # No version available
        'version': None,
        'files': {
            'plantlst.txt': 'https://plants.sc.egov.usda.gov/assets/docs/CompletePLANTSList/plantlst.txt'
        },
        'latest': True
    }
    return [entry]


def try_get_data_source_entry(log, data_source_id, func) -> List[Entry]:
    try:
        versions = func()
        print('Retrieved ' + str(len(versions)) + ' versions for data source "' + data_source_id + '"', file=log)
        return versions
    except Exception as e:
        print('Failed to retrieve data source "' + data_source_id + '" status', e, file=log)
        return DEFAULT


if __name__ == '__main__':
    with open('update-log.txt', 'w', encoding='utf-8') as log:
        print('Updating data sources at ' + datetime.now().isoformat(), file=log)
        result = {
            'AACT': try_get_data_source_entry(log, 'AACT', get_aact_entry),
            'CanadianNutrientFile': try_get_data_source_entry(log, 'CanadianNutrientFile',
                                                              get_canadian_nutrient_file_entry),
            'CancerDrugsDB': try_get_data_source_entry(log, 'CancerDrugsDB', get_cancer_drugs_db_entry),
            'DGIdb': try_get_data_source_entry(log, 'DGIdb', get_dgidb_entry),
            'DrugBank': try_get_data_source_entry(log, 'DrugBank', get_drugbank_entry),
            'DrugCentral': try_get_data_source_entry(log, 'DrugCentral', get_drugcentral_entry),
            'EMA': try_get_data_source_entry(log, 'EMA', get_ema_entry),
            'Gene2Phenotype': try_get_data_source_entry(log, 'Gene2Phenotype', get_gene2phenotype_entry),
            'GeneOntology': try_get_data_source_entry(log, 'GeneOntology', get_gene_ontology_entry),
            'GWASCatalog': try_get_data_source_entry(log, 'GWASCatalog', get_gwas_catalog_entry),
            'HGNC': try_get_data_source_entry(log, 'HGNC', get_hgnc_entry),
            'HPO': try_get_data_source_entry(log, 'HPO', get_hpo_entry),
            'ITIS': try_get_data_source_entry(log, 'ITIS', get_itis_entry),
            'KEGG': try_get_data_source_entry(log, 'KEGG', get_kegg_entry),
            'MED-RT': try_get_data_source_entry(log, 'MED-RT', get_med_rt_entry),
            'Mondo': try_get_data_source_entry(log, 'Mondo', get_mondo_entry),
            'NDF-RT': try_get_data_source_entry(log, 'NDF-RT', get_ndf_rt_entry),
            'OpenTargets': try_get_data_source_entry(log, 'OpenTargets', get_open_targets_entry),
            'PathwayCommons': try_get_data_source_entry(log, 'PathwayCommons', get_pathway_commons_entry),
            'PharmGKB': try_get_data_source_entry(log, 'PharmGKB', get_pharmgkb_entry),
            'ReDO-DB': try_get_data_source_entry(log, 'ReDO-DB', get_redo_db_entry),
            'ReDOTrialsDB': try_get_data_source_entry(log, 'ReDOTrialsDB', get_redo_trials_db_entry),
            'Sider': try_get_data_source_entry(log, 'Sider', get_sider_entry),
            'UNII': try_get_data_source_entry(log, 'UNII', get_unii_entry),
            'UniProt': try_get_data_source_entry(log, 'UniProt', get_uniprot_entry),
            'USDA-PLANTS': try_get_data_source_entry(log, 'USDA-PLANTS', get_usda_plants_entry),
        }
        with open('result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, sort_keys=True)
        with open('result.min.json', 'w', encoding='utf-8') as f:
            json.dump(result, f)
