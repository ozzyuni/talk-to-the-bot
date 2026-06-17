from setuptools import find_packages, setup

package_name = 'talk_to_the_bot_stt'

setup(
    name=package_name,
    version='0.2.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name, ['config/listener_config.json']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='parikkao',
    maintainer_email='ossi.parikka@tuni.fi',
    description='Records and transcribes audio input',
    license='GPL-3.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'stt = talk_to_the_bot_stt.listener_srv:main',
            'test = talk_to_the_bot_stt.listener:main',
            'transcriber = talk_to_the_bot_stt.transcriber_srv:main',
            'transcriber_tcp_srv = talk_to_the_bot_stt.transcriber_tcp_srv:main',
            'transcriber_tcp_cli = talk_to_the_bot_stt.transcriber_tcp_cli:main'
        ],
    },
)
