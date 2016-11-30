from setuptools import setup, find_packages

setup(
    name = "simproxy",
    version = "0.0.1",
    author = "Alan Shi",
    author_email = "alan@sinosims.com",

    packages = find_packages(), 
    include_package_data = True,

    url = "http://www.sinosims.com",
    description = "Simhub Proxy",
    
    entry_points = {
        'console_scripts': [ 'simproxy = simproxy.run:main' ]
    },
    install_requires = ["msgpack-python"],
)
