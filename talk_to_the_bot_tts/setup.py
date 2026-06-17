from setuptools import find_packages, setup

package_name = 'talk_to_the_bot_tts'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name, ['config/talker_config.json']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='parikkao',
    maintainer_email='ossi.parikka@tuni.fi',
    description='Text to speech',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'tts = talk_to_the_bot_tts.talker_srv:main'
        ],
    },
)
