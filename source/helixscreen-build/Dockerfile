FROM debian:trixie-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN echo 'Acquire::Retries "3";' >/etc/apt/apt.conf.d/80-retries && dpkg --add-architecture armhf && apt-get update && apt-get install -y --no-install-recommends build-essential crossbuild-essential-armhf git pkg-config ca-certificates make cmake python3 python3-pil file autoconf automake libtool flex bison ccache zip imagemagick librsvg2-bin libc6-dev:armhf libstdc++-14-dev:armhf libdrm-dev:armhf libinput-dev:armhf libudev-dev:armhf libssl-dev:armhf libsystemd-dev:armhf zlib1g-dev:armhf libusb-1.0-0-dev:armhf libbluetooth-dev:armhf libasound2-dev:armhf libjpeg62-turbo-dev:armhf && rm -rf /var/lib/apt/lists/*
ENV CROSS_COMPILE=arm-linux-gnueabihf- CC=arm-linux-gnueabihf-gcc CXX=arm-linux-gnueabihf-g++ AR=arm-linux-gnueabihf-gcc-ar STRIP=arm-linux-gnueabihf-strip RANLIB=arm-linux-gnueabihf-gcc-ranlib LD=arm-linux-gnueabihf-ld PKG_CONFIG_PATH=/usr/lib/arm-linux-gnueabihf/pkgconfig PKG_CONFIG_SYSROOT_DIR=/
RUN git config --global --add safe.directory '*'
WORKDIR /src
