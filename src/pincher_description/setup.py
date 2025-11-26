from setuptools import setup
from glob import glob
import os

package_name = 'pincher_description'

setup(
    name=package_name,
    version='0.0.0',
    packages=[],
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'urdf'),
         glob('urdf/*')),
        (os.path.join('share', package_name, 'meshes'),
         glob('meshes/*')),
        (os.path.join('share', package_name, 'rviz'),
         glob('rviz/*')),
        (os.path.join('share', package_name, 'launch'),
         glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='parallels',
    maintainer_email='parallels@todo.todo',
    description='URDF and meshes for the PhantomX Pincher robot.',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [],
    },
)
