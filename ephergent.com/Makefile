VPS_USER   = user
VPS_HOST   = your-vps-ip-or-hostname
VPS_PATH   = /var/www/ephergent.com/html

.PHONY: build deploy

build:
	npm run build

deploy: build
	rsync -avz --delete dist/ $(VPS_USER)@$(VPS_HOST):$(VPS_PATH)
