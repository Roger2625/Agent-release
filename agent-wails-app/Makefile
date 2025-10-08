.PHONY: dev build install clean frontend-install frontend-build

dev:
	wails dev

build:
	wails build

frontend-install:
	cd frontend && npm install

frontend-build:
	cd frontend && npm run build

install: frontend-install
	go mod download

clean:
	rm -rf build/
	rm -rf frontend/dist/
	rm -rf frontend/node_modules/

run: build
	./build/bin/agent-app
