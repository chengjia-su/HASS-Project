from setuptools import setup
from setuptools import find_packages
setup(
    name = 'Hass',
    version = '0.1',
    description = 'Openstack high availability software service(HASS)',
    author = 'chengjia',
    url = '',
    license = 'Apache-2.0',
    packages = find_packages(),
    py_modules = ['HassAPI'],
    entry_points = {'console_scripts': ['hass = HassAPI:main',],},
)