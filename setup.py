# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Invenio module that adds PID relations to the Invenio-PIDStore module."""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()
history = open('CHANGES.rst').read()

tests_require = [
    'check-manifest>=0.25',
    'coverage>=4.0',
    'isort>=4.2.2',
    'pydocstyle>=1.0.0',
    'pytest-cache>=1.0',
    'pytest-cov>=1.8.0',
    'pytest-pep8>=1.0.6',
    'pytest>=2.8.0',
]

extras_require = {
    'docs': [
        'Sphinx>=1.5.1',
    ],
    'tests': tests_require,
    'mysql': [
        'invenio-db[mysql,versioning]>=1.0.0b3',
    ],
    'postgresql': [
        'invenio-db[postgresql,versioning]>=1.0.0b3',
    ],
    'sqlite': [
        'invenio-db[versioning]>=1.0.0b3',
    ],
    'records': [
        'invenio-deposit>=1.0.0a7',
        'invenio-records>=1.0.0b1',
        # FIXME: Added because requirements-builder does not search
        # recursively lowest dependencies.
        'invenio-records-ui>=1.0.0a8',
        'invenio-records-rest>=1.0.0a17',
        'invenio-accounts>=1.0.0b5',
        'Flask-WTF>=0.13.1',
        # Needed in order to have correct alembic upgrade.
        'invenio-oauth2server>=1.0.0a14',
        'invenio-records-files>=1.0.0a9',
        'invenio-files-rest>=1.0.0a15',
    ],
    'indexer': [
        'invenio-indexer>=1.0.0a9',
    ],
}

extras_require['all'] = []
for name, reqs in extras_require.items():
    if name in ('mysql', 'postgresql', 'sqlite'):
        continue
    extras_require['all'].extend(reqs)

setup_requires = [
    'Babel>=1.3',
    'pytest-runner>=2.6.2',
]

install_requires = [
    'Flask-BabelEx>=0.9.2',
    'invenio-pidstore>=1.0.0b1',
    'invenio-rest[cors]>=1.0.0a10',
    'SQLAlchemy>=1.0.9',
    'marshmallow>=2.12.2',
    'six>=1.10',
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
    license='GPLv2',
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
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Development Status :: 1 - Planning',
    ],
)
