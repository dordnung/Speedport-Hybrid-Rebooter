## Speedport Hybrid Rebooter

### This will restart your Speedport Hybrid Router.    
### With this you can for example restart your Speedport at a specific time interval (Crontab on Linux).    
### Your device have to be in the local network and have to be access to the configurator!
    
## Install Instruction         
- **Linux** (Type commands in terminal):
     - Install requirements:
         - Install Python (2.7):  sudo apt-get install build-essential python
         - Download PyCrypto:     wget https://github.com/dlitz/pycrypto/archive/v2.7a1.zip
         - Unzip PyCrypto:        unzip v2.7a1.zip && cd pycrypto-2.7a1
         - Install PyCrypto:      sudo python setup.py install
     - Set Config in Python script!
     - This will restart your Speedport Hybrid: python speedport-rebooter.py
- **Windows**:
     - Install requirements:
         - Install Python (2.7):  https://www.python.org/downloads/
         - Download PyCrypto:     https://github.com/dlitz/pycrypto/archive/v2.7a1.zip
         - Unzip PyCrypto and go into folder
         - Install PyCrypto:  python setup.py install
         - You may need a compiler environment like Visual Studio!
     - Set Config in Python script!
     - This will restart your Speedport Hybrid: python speedport-rebooter.py