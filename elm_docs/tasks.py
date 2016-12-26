'''
'''
from typing import List, Optional
import os
import os.path
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import subprocess

from elm_docs import elm_package_overlayer_path
from elm_docs import elm_package
from elm_docs.elm_package import ElmPackage, ModuleName


PAGE_PACKAGE_TEMPLATE = '''
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8">
    <link rel="shortcut icon" size="16x16, 32x32, 48x48, 64x64, 128x128, 256x256" href="/assets/favicon.ico">
    <link rel="stylesheet" href="/assets/highlight/styles/default.css">
    <link rel="stylesheet" href="/assets/style.css">
    <script src="/assets/highlight/highlight.pack.js"></script>
    <script src="/artifacts/Page-Package.js"></script>
  </head>
  <body>
  <script>
    var page = Elm.Page.Package.fullscreen({flags});
  </script>
  </body>
</html>
'''

def get_page_package_flags(package: ElmPackage, module : Optional[str] = None):
    flags = {
        'user': package.user,
        'project': package.project,
        'version': package.version,
        'allVersions': [package.version],
        'moduleName': module,
    }
    return flags


def build_package_page(package: ElmPackage, output_path: Path, module : Optional[str] = None):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(PAGE_PACKAGE_TEMPLATE.format(
            flags=get_page_package_flags(package, module)
        ))


def link_latest_package_dir(package_dir: Path, link_path: Path):
    os.makedirs(package_dir, exist_ok=True)
    link_path.symlink_to(package_dir, target_is_directory=True)


def copy_package_readme(package_readme: Path, output_path: Path):
    if package_readme.is_file():
        shutil.copy(package_readme, output_path)


def build_package_docs_json(package: ElmPackage, output_path: Path, package_modules: List[ModuleName]):
    here = os.path.abspath(os.path.dirname(__file__))
    # todo: use my own elm
    elm_make = os.environ['ELM_MAKE']
    elm_package_with_exposed_modules = {**package.description, **{'exposed-modules': package_modules}}
    overlayer_path = elm_package_overlayer_path()
    with TemporaryDirectory() as tmpdir:
        elm_package_path = Path(tmpdir) / elm_package.DESCRIPTION_FILENAME
        with open(elm_package_path, 'w') as f:
            json.dump(elm_package_with_exposed_modules, f)
        env = {
            **os.environ,
            **{
                'USE_ELM_PACKAGE': elm_package_path,
                'INSTEAD_OF_ELM_PACKAGE': elm_package.description_path(package),
                'DYLD_INSERT_LIBRARIES': overlayer_path,
            }
        }
        subprocess.check_call([elm_make, '--yes', '--docs', output_path], cwd=package.path, env=env)


def build_elm_package_docs(output_dir: str, package: ElmPackage):
    package_identifier = '/'.join((package.user, package.project, package.version))

    package_docs_root = Path(output_dir) / 'packages' / package.user / package.project / package.version

    # package index page
    package_index_output = package_docs_root / 'index.html'
    yield {
        'basename': 'package_page:' + package_identifier,
        'actions': [(build_package_page, (package, package_index_output))],
        'targets': [package_index_output],
        #'file_deps': [module['source_file']] #todo
    }

    # package readme
    readme_filename = 'README.md'
    package_readme = package.path / readme_filename
    output_readme_path = package_docs_root / readme_filename
    yield {
        'basename': 'package_readme:' + package_identifier,
        'actions': [(copy_package_readme, (package_readme, output_readme_path))],
        'targets': [output_readme_path],
        'file_deps': [package_readme],
    }

    # link from /latest
    latest_path = package_docs_root.parent / 'latest'
    yield {
        'basename': 'package_latest_link:' + package_identifier,
        'actions': [(link_latest_package_dir, (package_docs_root, latest_path))],
        'targets': [latest_path],
        #'file_deps': [], # todo
    }

    # todo: make mount point configurable: prepend path in page package html and in generated js

    # module pages
    package_modules = list(elm_package.iter_package_modules(package))
    for module in package_modules:
        module_output = package_docs_root / module.replace('.', '-')
        yield {
            'basename': 'module_page:{}:{}'.format(package_identifier, module),
            'actions': [(build_package_page, (package, module_output, module))],
            'targets': [module_output],
            #'file_deps': [module['source_file']] #todo
        }

    # package documentation.json
    docs_json_path = package_docs_root / 'documentation.json'
    yield {
        'basename': 'package_docs_json:' + package_identifier,
        'actions': [(build_package_docs_json, (package, docs_json_path, package_modules))],
        'targets': [docs_json_path],
        #'file_deps': [all_elm_files_in_source_dirs] # todo
    }


def create_tasks(output_dir: str, project_paths: List[str]):
    # todo: yield task for building elm apps and copying assets
    # todo: yield task for all-packages
    # todo: yield task for new-packages

    for elm_package in elm_packages:

    packages = list(map(elm_package.from_path,
                            map(lambda path: Path(path).resolve(), project_paths)))
    for package in packages:
        # todo: yield task to install elm for this package
        for task in build_elm_package_docs(output_dir, package):
            yield task



def task_elm_docs():
    project_paths = [
        '.',
        'ui',
    ]
    create_tasks(project_paths)
