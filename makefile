 .PHONY: up down

up:
	export SNOMED_HOST_PATH=/home/sub-escanor/Public/Data/SNOMEDCT/International-Edition && docker compose up

down:
	export SNOMED_HOST_PATH=/home/sub-escanor/Public/Data/SNOMEDCT/International-Edition && docker compose down
