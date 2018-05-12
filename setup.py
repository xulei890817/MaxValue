from setuptools import setup
from setuptools import setup, find_packages, __version__ as setuptools_version

setup(
    name='MaxValue',
    version='0.0.2',
    packages=['MaxValue', 'MaxValue.conf', 'MaxValue.plan', 'MaxValue.utils', 'MaxValue.market', 'MaxValue.lancher', 'MaxValue.watcher', 'MaxValue.api_handler.apis', 'MaxValue.api_handler.base'],
    url='https://github.com/xulei890817/MaxValue.git',
    license='',
    author='leixu',
    author_email='lei.xu@grandhonor.net',
    description='treasure in the deep sea.find the light in dark.',
    python_requires='>=3.5',
    classifiers=[
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    install_requires=[
        "RetryMe",
        "arrow",
        "bitmex",
        "aiohttp",
        "requests",
    ],
)
