#!/usr/bin/env bash


if [ $TRAVIS_OS_NAME == "linux" ]
then
    export XVFBARGS="-screen 0 1280x1024x24"
    export DISPLAY=:99.0
    sh -e /etc/init.d/xvfb start
    sleep 3
fi

if [ $TRAVIS_OS_NAME == "osx" ]
then
    brew tap homebrew/versions
    brew update
    brew install libsodium
    ## Ensure your brew QT version is up to date. (brew install qt -> qt 4.8)
    brew install qt5
    brew install pyenv-virtualenv
    pyenv update
    pip install PyQt5
elif [ $TRAVIS_OS_NAME == "linux" ]
then
    # sudo apt-get update
    # sudo apt-get install -qq -y libxcb1 libxcb1-dev libx11-xcb1 libx11-xcb-dev libxcb-keysyms1 libxcb-keysyms1-dev libxcb-image0 \
    #         libxcb-image0-dev libxcb-shm0 libxcb-shm0-dev libxcb-icccm4 libxcb-icccm4-dev \
    #         libxcb-xfixes0-dev libxrender-dev libxcb-shape0-dev libxcb-randr0-dev libxcb-render-util0 \
    #         libxcb-render-util0-dev libxcb-glx0-dev libgl1-mesa-dri libegl1-mesa libpcre3 libgles2-mesa-dev \
    #         freeglut3-dev libfreetype6-dev xorg-dev xserver-xorg-input-void xserver-xorg-video-dummy xpra libosmesa6-dev \
    #         curl libdbus-1-dev libdbus-glib-1-dev autoconf automake libtool libgstreamer-plugins-base0.10-0
    # wget https://download.qt.io/official_releases/qt/5.5/5.5.1/qt-opensource-linux-x64-5.5.1.run
    # chmod +x qt-opensource-linux-x64-5.5.1.run
    # ./qt-opensource-linux-x64-5.5.1.run --script $HOME/build/duniter/sakia/ci/travis/qt-installer-noninteractive.qs

    pip install PyQt5
    wget http://archive.ubuntu.com/ubuntu/pool/universe/libs/libsodium/libsodium13_1.0.1-1_amd64.deb
    sudo dpkg -i libsodium13_1.0.1-1_amd64.deb
    rm -r ~/.pyenv
    git clone https://github.com/yyuu/pyenv.git ~/.pyenv
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bash_profile
    echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bash_profile

    ldconfig -p
fi

eval "$(pyenv init -)"

pyenv install --list
if [ $TRAVIS_OS_NAME == "osx" ]
then
    env PYTHON_CONFIGURE_OPTS="--enable-framework" pyenv install $PYENV_PYTHON_VERSION
elif [ $TRAVIS_OS_NAME == "linux" ]
then
    PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install $PYENV_PYTHON_VERSION
fi

pyenv shell $PYENV_PYTHON_VERSION

cd $HOME

wget http://ufpr.dl.sourceforge.net/project/pyqt/sip/sip-4.17/sip-4.17.tar.gz
file sip-4.17.tar.gz
gzip -t sip-4.17.tar.gz
tar xzf sip-4.17.tar.gz
cd sip-4.17/
python configure.py
make && make install
pyenv rehash

cd $HOME
pyenv shell $PYENV_PYTHON_VERSION
wget http://ufpr.dl.sourceforge.net/project/pyqt/PyQt5/PyQt-5.5.1/PyQt-gpl-5.5.1.tar.gz
file PyQt-gpl-5.5.1.tar.gz
gzip -t PyQt-gpl-5.5.1.tar.gz
tar xzf PyQt-gpl-5.5.1.tar.gz
cd PyQt-gpl-5.5.1/
if [ $TRAVIS_OS_NAME == "osx" ]
then
    python configure.py --confirm-license \
        --enable QtCore \
        --enable QtWidgets \
        --enable QtGui \
        --enable QtSvg \
        --enable QtWebChannel \
        --enable QtWebEngineWidgets \
        --enable QtNetwork \
        --enable QtPrintSupport \
        --enable QtTest \
        --pyuic5-interpreter /Users/travis/.pyenv/versions/$PYENV_PYTHON_VERSION/bin/python3.5 \
        --sip /Users/travis/.pyenv/versions/$PYENV_PYTHON_VERSION/Python.framework/Versions/3.5/bin/sip
elif [ $TRAVIS_OS_NAME == "linux" ]
then
    python configure.py --qmake "/tmp/qt/5.5/5.5/gcc_64/bin/qmake" --confirm-license  \
        --enable QtCore \
        --enable QtWidgets \
        --enable QtGui \
        --enable QtSvg \
        --enable QtWebChannel \
        --enable QtWebEngineWidgets \
        --enable QtNetwork \
        --enable QtPrintSupport \
        --enable QtTest \
        --pyuic5-interpreter /home/travis/.pyenv/versions/$PYENV_PYTHON_VERSION/bin/python3.5 \
        --sip /home/travis/.pyenv/versions/3.5.2/bin/sip
fi

make -j 2 && make install
pyenv rehash
