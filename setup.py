import setuptools
reqs = ['utils-s', 'pydub']
version = '2.9'

setuptools.setup(
    name='playerFramework',
    version=version,
    description="A Bridge between compiled players and Python",
    packages=setuptools.find_packages(),
    install_requires=reqs
)
