FROM python:latest
WORKDIR /PfsenseBot
LABEL Maintainer="eimparas"
COPY pfbotV2.py /PfsenseBot
# Now the structure looks like this '/PfsenseBot/pfbotV2.py'
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get upgrade python3-pip -y
RUN pip3 install nextcord requests
CMD ["python3", "pfbotV2.py"]