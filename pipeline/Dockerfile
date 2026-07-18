FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    bwa \
    samtools \
    build-essential \
    zlib1g-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://raw.githubusercontent.com/lh3/wgsim/master/wgsim.c -O /tmp/wgsim.c \
    && wget https://raw.githubusercontent.com/lh3/wgsim/master/kseq.h -O /tmp/kseq.h \
    && gcc -g -O2 -o /usr/local/bin/wgsim /tmp/wgsim.c -lz -lm \
    && rm /tmp/wgsim.c /tmp/kseq.h

WORKDIR /work