#!/bin/bash

username="adsl_monitor"
script_file="Get_Vigor165_DSL_Status.py"
script_dest="/usr/local/bin/$script_file"

check() {
    # Check if the user exists
    if id "$username" &>/dev/null; then
        echo "User '$username' exists."
    else
        echo "User '$username' does not exist."
    fi

    # Check if the systemd service file exists
    service_file="/etc/systemd/system/adsl_monitoring.service"
    if [ -f "$service_file" ]; then
        echo "Service file '$service_file' exists."
    else
        echo "Service file '$service_file' does not exist."
    fi

    # Check if the script file in /usr/local/bin exists
    if [ -f "$script_dest" ]; then
        echo "Script file '$script_dest' exists."
    else
        echo "Script file '$script_dest' does not exist."
    fi
}

install() {
    # Check if the user exists
    if id "$username" &>/dev/null; then
        echo "User '$username' already exists."
    else
        echo "Creating user '$username'..."
        sudo useradd --system --no-create-home --shell /bin/false "$username"
        echo "User '$username' created successfully."
    fi

    # Create directory and copy API key file
    key_dir="/etc/adsl_monitoring"
    key_file="Philips_Hue_API_Key.txt"
    
    if [ ! -d "$key_dir" ]; then
        sudo mkdir "$key_dir"
    fi

    if [ -f "$key_file" ]; then
        sudo cp "$key_file" "$key_dir/$key_file"
        sudo chown "$username:$username" "$key_dir/$key_file"
        sudo chmod 600 "$key_dir/$key_file"
    else
        echo "Error: File '$key_file' does not exist."
        exit 1
    fi

    # Install the Python script
    sudo cp "$script_file" "$script_dest"
    sudo chmod 755 "$script_dest"

    # Install systemd service
    sudo cp adsl_monitoring.service /etc/systemd/system/adsl_monitoring.service
    sudo systemctl daemon-reload
    sudo systemctl enable adsl_monitoring.service
    sudo systemctl start adsl_monitoring.service
}

remove() {
    # Stop and disable the service
    sudo systemctl stop adsl_monitoring.service
    sudo systemctl disable adsl_monitoring.service

    # Reset the failed status of the service
    sudo systemctl reset-failed adsl_monitoring.service

    # Remove the service file
    sudo rm -f /etc/systemd/system/adsl_monitoring.service
    sudo systemctl daemon-reload

    # Delete the user
    sudo userdel "$username"

    # Remove the directory and its contents
    sudo rm -rf /etc/adsl_monitoring

    # Remove the Python script
    sudo rm -f "$script_dest"
}

case "$1" in
    --check)
        check
        ;;
    --install)
        install
        ;;
    --remove)
        remove
        ;;
    *)
        echo "Usage: $0 {--check|--install|--remove}"
        exit 1
        ;;
esac

exit 0
