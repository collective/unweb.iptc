from setuptools import setup, find_packages
import os


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

long_description = (
    read('README.rst')
    + '\n' +
    read('CHANGES.rst')
    + '\n' +
    read('docs/CONTRIBUTORS.rst')
    )


setup(name='unweb.iptc',
      version='0.4',
      description="IPTC metadata extraction and storage for images in Plone",
      long_description=long_description,
      # Get more strings from
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        "Topic :: Multimedia :: Graphics",
        ],
      keywords='image photo metadata IPTC keywords plone zope',
      author='Dimitris Moraitis',
      author_email='dimo@unweb.me',
      url='http://pypi.python.org/pypi/unweb.iptc/',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['unweb'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'Products.CMFPlone',
          'Products.ATContentTypes',
          'IPTCInfo',
          'py-dateutil',
      ],
      extras_require={
          'test': ['plone.app.testing',
                   'interlude', ]
      },
      entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
