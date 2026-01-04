#!/usr/bin/env bash

# colors
NO_FORMAT="\e[0m"
F_BOLD="\e[1m"

if [[ $# -ne 2 ]]; then
    echo "You need to specify the script you want to install!"
    echo "Usage: $0 <operation> <script_name>."
    echo -e "operation: Can either be ${F_BOLD}run${NO_FORMAT} or ${F_BOLD}prepare${NO_FORMAT}" 
    echo -e "script_name: Can be ${F_BOLD}influxfeeder${NO_FORMAT}, ${F_BOLD}modembot${NO_FORMAT} or ${F_BOLD}pfsensebot${NO_FORMAT}"
    exit 1
fi

# convert operation and script name to lower case
operation="${1,,}"
script="${2,,}"

if [[ "$operation" == "prepare" ]]; then
    if [[ "$script" == "influxfeeder" ]]; then
        if [[ -f "Grafana Dashboard/config.cfg.sample" ]]; then
            echo "Please fill in your credentials in the config file of InfluxDB feeder!"
            exit 3
        fi
        mv "Grafana Dashboard/InfluxdbFeeder.py" .
    elif [[ "$script" == "modembot" ]]; then
        if [[ -f "ModemBot/config.cfg.sample" ]]; then
            echo "Please fill in your credentials in the config file of Modem bot!"
            exit 3
        fi
        mv "ModemBot/modemBot.py" .
    elif [[ "$script" == "pfsensebot" ]]; then
        if [[ -f "PfsenseBot/config.cfg.sample" ]]; then
            echo "Please fill in your credentials in the config file of Pfsense bot!"
            exit 3
        fi
        mv "PfsenseBot/PFsenseBot.py" .
    else
        echo "Invalid script option!"
        exit 2
    fi

    if [[ ! -d ".venv" ]]; then
        echo "Installing dependencies, please wait..."
        python3 -m venv .venv
        source .venv/bin/activate
        pip3 install -r requirements.txt
        echo "Done!"
        deactivate
    fi

elif [[ "$operation" == "run" ]]; then
    if [[ -f .venv/bin/activate ]]; then
        source .venv/bin/activate
    else
        echo "Virtual environment not found! Run prepare first."
        exit 1
    fi
    
    # deactivate venv on exit
    trap 'deactivate' EXIT

    source .venv/bin/activate
    if [[ "$script" == "influxfeeder" ]]; then
        python3 -u "InfluxdbFeeder.py"
    elif [[ "$script" == "modembot" ]]; then
        python3 -u "modemBot.py"
    elif [[ "$script" == "pfsensebot" ]]; then
        python3 -u "PFsenseBot.py"
    else
        echo "Invalid script option!"
        exit 2
    fi
else
    echo "Invalid operation option!"
    exit 1
fi