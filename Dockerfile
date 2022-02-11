ARG ARCH=amd64

FROM $ARCH/python:3.9-alpine

EXPOSE 443
EXPOSE 5223
EXPOSE 8007
EXPOSE 8883

COPY requirements.txt /requirements.txt

# install required python packages
RUN pip3 install -r requirements.txt

WORKDIR /bumper

# Copy only required folders instead of all
COPY bumper/ bumper/

ENTRYPOINT ["python3", "-m", "bumper"]
