from setuptools import setup

setup(
    name = 'Hass',
    version = '0.1',
    description = 'Openstack high availability software service(HASS)',
    author = 'chengjia',
    url = '',
    license = 'Apache-2.0',
    packages = ['HassAPI'],
    entry_points = {'console_scripts': ['hass = HassAPI.HassAPI',],},
)