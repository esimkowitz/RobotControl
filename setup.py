try:
    # Try using ez_setup to install setuptools if not already installed.
    from ez_setup import use_setuptools
    use_setuptools()
except ImportError:
    # Ignore import error and assume Python 3 which already has setuptools.
    pass

from setuptools import setup, find_packages


setup(name='RobotControl',
      version='0.1.0',
      author='Evan Simkowitz',
      author_email='esimkowitz@wustl.edu',
      description='A simple controller for a simple robot.',
      license='MIT',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Operating System :: POSIX :: Linux',
          'License :: OSI Approved :: MIT License',
          'Intended Audience :: Developers',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Topic :: Software Development',
          'Topic :: System :: Hardware'],
      url='https://github.com/esimkowitz/RobotControl/',
      dependency_links=[
          'https://github.com/adafruit/Adafruit-Motor-HAT-Python-Library/tarball/master'],
      install_requires=['Flask>=0.12.2', 'Flask-SocketIO>=2.9.1'],
      packages=find_packages(),
      zip_safe=False)
