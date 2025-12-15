FROM debian:bookworm-slim

RUN apt-get update \
    && \
    apt-get install -y --no-install-recommends --no-install-suggests \
        python3 \
        python3-pip \
        lib32stdc++6 \
        lib32gcc-s1 \
        libcurl4 \
        wget \
        ca-certificates \
        curl \
        libstdc++6 \
        libssl3 \
        libc6 \
        git \
        zip \
        unzip \
    && \
    apt-get remove --purge -y \
    && \
    apt-get clean autoclean \
    && \
    apt-get autoremove -y \
    && \
    rm -rf /var/lib/apt/lists/*

RUN wget https://github.com/SteamRE/DepotDownloader/releases/latest/download/DepotDownloader-linux-x64.zip -O /tmp/depotdownloader.zip \
    && \
    mkdir -p /usr/bin/depotdownloader \
    && \
    unzip /tmp/depotdownloader.zip -d /tmp/depotdownloader \
    && \
    mv /tmp/depotdownloader/DepotDownloader /usr/bin/DepotDownloader \
    && \
    rm /tmp/depotdownloader.zip
    
RUN pip install --break-system-packages dotenv
RUN ls /usr/bin/depotdownloader
EXPOSE 2302/udp
EXPOSE 2303/udp
EXPOSE 2304/udp
EXPOSE 2305/udp
EXPOSE 2306/udp
RUN mkdir /arma
WORKDIR /arma

STOPSIGNAL SIGINT
COPY *.py /

CMD ["python3", "/launch.py"]