from typing import List
from pathlib import Path
import json

from elm_doc.elm_project import ElmPackage
from elm_doc import elm_project
from elm_doc import page_template


def write_index_page(output_path: Path, mount_point: str = ''):
    with open(str(output_path), 'w') as f:
        f.write(page_template.render(mount_point=mount_point))


def write_search_json(packages: List[ElmPackage], output_path: Path):
    all_packages = map(
        lambda package: {
            'name': package.name,
            'summary': package.summary,
            'license': package.license,
            'versions': [package.version],
        },
        packages)
    with open(str(output_path), 'w') as f:
        json.dump(list(all_packages), f)


def write_new_packages(packages: List[ElmPackage], output_path: Path):
    new_packages = map(lambda package: package.name, packages)
    with open(str(output_path), 'w') as f:
        json.dump(list(new_packages), f)


def create_catalog_tasks(packages: List[ElmPackage], output_path: Path, mount_point: str = ''):
    # index
    index_path = output_path / 'index.html'
    yield {
        'basename': 'index',
        'actions': [(write_index_page, (index_path, mount_point))],
        'targets': [index_path],
        'uptodate': [True],
    }

    # search.json
    search_json_path = output_path / 'search.json'
    yield {
        'basename': 'search_json',
        'actions': [(write_search_json, (packages, search_json_path))],
        'targets': [search_json_path],
        'file_dep': [package.json_path for package in packages],
    }

    # new-packages
    new_packages_path = output_path / 'new-packages'
    yield {
        'basename': 'new_packages',
        'actions': [(write_new_packages, (packages, new_packages_path))],
        'targets': [new_packages_path],
        'file_dep': [package.json_path for package in packages],
    }
