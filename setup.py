import setuptools
reqs = ['utils-s', 'pydub']
version = '3.0'

setuptools.setup(
    name='playerFramework',
    version=version,
    description="A simple way to play audio in Python.",
    packages=setuptools.find_packages(),
    install_requires=reqs
)
