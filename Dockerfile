FROM debian:slim

RUN apt-get update && apt-get install -y ffmpeg