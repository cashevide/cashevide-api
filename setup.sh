#!/bin/bash

copy_config() {

	local example_file=$1
	local target_file=$2

	if [ ! -f "$target_file" ]; then
		if [ -f "$example_file" ]; then
			cp "$example_file" "$target_file"
			echo "$target_file Created"
		else
			echo "$example_file not found"
		fi
	else
		echo "$target_file already exist"
	fi
}

copy_config ".env.example" ".env"
copy_config "docker-compose.override.example.yml" "docker-compose.override.yml"
copy_config "nginx/dev.example.conf" "nginx/dev.conf"
