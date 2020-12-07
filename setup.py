# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module that adds PID relations to the Invenio-PIDStore module."""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()
history = open('CHANGES.rst').read()

tests_require = [
    'pytest-invenio>=1.4.0,<2.0.0',
]

invenio_db_version = '>=1.0.4,<2.0.0'
invenio_search_version = '>=1.3.1,<1.4.0'
extras_require = {
    'docs': [
        'Sphinx>=3',
    ],
    # Invenio-Search
    'elasticsearch6': [
        'invenio-search[elasticsearch6]{}'.format(invenio_search_version)
    ],
    'elasticsearch7': [
        'invenio-search[elasticsearch7]{}'.format(invenio_search_version)
    ],
    'tests': tests_require,
    'mysql': [
        'invenio-db[mysql,versioning]{}'.format(invenio_db_version)
    ],
    'postgresql': [
        'invenio-db[postgresql,versioning]{}'.format(invenio_db_version)
    ],
    'sqlite': [
        'invenio-db[versioning]{}'.format(invenio_db_version)
    ],
    'records': [
        'invenio-records>=1.3.2',
        # FIXME: Added because requirements-builder does not search
        # recursively lowest dependencies.
        'invenio-records-ui>=1.1.0',
    ],
    'indexer': [
        'invenio-indexer>=1.1.2',
    ],
}

extras_require['all'] = []
for name, reqs in extras_require.items():
    if name in ('mysql', 'postgresql', 'sqlite', 'elasticsearch6',
                'elasticsearch7'):
        continue
    extras_require['all'].extend(reqs)

setup_requires = [
    'Babel>=1.3',
    'pytest-runner>=2.6.2',
]

install_requires = [
    'invenio-base>=1.2.3',
    'invenio-i18n>=1.2.0',
    'invenio-pidstore>=1.0.0',
    'marshmallow>=3.3.0,<4.0.0',
]

packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('invenio_pidrelations', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='invenio-pidrelations',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='invenio pidstore persistent identifier relations',
    license='MIT',
    author='CERN',
    author_email='info@inveniosoftware.org',
    url='https://github.com/inveniosoftware/invenio-pidrelations',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'invenio_base.apps': [
            'invenio_pidrelations = invenio_pidrelations:InvenioPIDRelations',
        ],
        'invenio_base.api_apps': [
            'invenio_pidrelations = invenio_pidrelations:InvenioPIDRelations',
        ],
        'invenio_db.alembic': [
            'invenio_pidrelations = invenio_pidrelations:alembic',
        ],
        'invenio_db.models': [
            'invenio_pidrelations = invenio_pidrelations.models',
        ],
        'invenio_i18n.translations': [
            'messages = invenio_pidrelations',
        ],
    },
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Development Status :: 1 - Planning',
    ],
)
