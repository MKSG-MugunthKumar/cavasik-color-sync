.PHONY: help install install-deps run run-scheme run-bg test test-dbus enable-cavasik-dbus service-install service-uninstall service-start service-stop service-status service-restart service-logs clean list-schemes

# Default target
help:
	@echo "Cavasik Color Sync - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  make install          - Install dependencies and setup service"
	@echo "  make install-deps     - Install Python dependencies only"
	@echo "  make run              - Run script with default config"
	@echo "  make run-scheme       - Run with specific scheme (e.g., SCHEME=neon)"
	@echo "  make run-bg           - Run in background using nohup"
	@echo "  make test             - Run all tests"
	@echo "  make test-dbus        - Test DBus connection to Cavasik"
	@echo "  make list-schemes     - List all available color schemes"
	@echo "  make enable-cavasik-dbus - Enable DBus colors in Cavasik"
	@echo "  make service-install  - Install as systemd user service"
	@echo "  make service-uninstall - Uninstall systemd user service"
	@echo "  make service-start    - Start the systemd service"
	@echo "  make service-stop     - Stop the systemd service"
	@echo "  make service-restart  - Restart the systemd service"
	@echo "  make service-status   - Check service status"
	@echo "  make service-logs     - View service logs"
	@echo "  make clean            - Clean cache and temporary files"
	@echo ""
	@echo "Examples:"
	@echo "  make run-scheme SCHEME=neon"
	@echo "  make install && make service-start"

# Install dependencies
install-deps:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt
	@echo "Dependencies installed successfully!"

# Full installation
install: install-deps
	@echo ""
	@echo "Installation complete!"
	@echo "Next steps:"
	@echo "  1. Enable DBus colors in Cavasik: make enable-cavasik-dbus"
	@echo "  2. Test the connection: make test-dbus"
	@echo "  3. Run the script: make run"
	@echo "  4. (Optional) Install as service: make service-install"

# Run the script
run:
	@echo "Running Cavasik Color Sync..."
	python3 cavasik-color-sync.py

# Run with specific color scheme
run-scheme:
	@if [ -z "$(SCHEME)" ]; then \
		echo "Error: Please specify SCHEME (e.g., make run-scheme SCHEME=neon)"; \
		echo "Available schemes: dominant_bg, neon, black_bg, gradient_reverse"; \
		exit 1; \
	fi
	@echo "Running with color scheme: $(SCHEME)"
	python3 cavasik-color-sync.py --scheme $(SCHEME)

# Run in background
run-bg:
	@echo "Starting Cavasik Color Sync in background..."
	@nohup python3 cavasik-color-sync.py > /tmp/cavasik-color-sync/nohup.log 2>&1 &
	@echo "Started! PID: $$!"
	@echo "Logs: /tmp/cavasik-color-sync/cavasik-sync.log"

# List available color schemes
list-schemes:
	python3 cavasik-color-sync.py --list-schemes

# Test DBus connection
test-dbus:
	@echo "Testing DBus connection to Cavasik..."
	python3 test-dbus.py

# Run all tests
test: test-dbus
	@echo ""
	@echo "All tests completed!"

# Enable DBus colors in Cavasik (Flatpak)
enable-cavasik-dbus:
	@echo "Enabling DBus colors in Cavasik..."
	@if command -v flatpak >/dev/null 2>&1; then \
		flatpak run --command=gsettings io.github.TheWisker.Cavasik set io.github.TheWisker.Cavasik dbus-colors true; \
		echo "DBus colors enabled!"; \
		echo "Verifying..."; \
		flatpak run --command=gsettings io.github.TheWisker.Cavasik get io.github.TheWisker.Cavasik dbus-colors; \
	else \
		echo "Error: flatpak not found. Please enable DBus colors manually in Cavasik preferences (Ctrl+P)."; \
		exit 1; \
	fi

# Install systemd service
service-install:
	@echo "Installing systemd user service..."
	@mkdir -p ~/.config/systemd/user
	@# Update service file with correct path
	@sed "s|%h/dev/MKSG/oss/cavasik-dbus/cavasik-color-sync.py|$(PWD)/cavasik-color-sync.py|g" \
		cavasik-color-sync.service > ~/.config/systemd/user/cavasik-color-sync.service
	@systemctl --user daemon-reload
	@echo "Service installed!"
	@echo "To enable at startup: systemctl --user enable cavasik-color-sync.service"
	@echo "To start now: make service-start"

# Uninstall systemd service
service-uninstall:
	@echo "Uninstalling systemd user service..."
	@systemctl --user stop cavasik-color-sync.service 2>/dev/null || true
	@systemctl --user disable cavasik-color-sync.service 2>/dev/null || true
	@rm -f ~/.config/systemd/user/cavasik-color-sync.service
	@systemctl --user daemon-reload
	@echo "Service uninstalled!"

# Start service
service-start:
	@echo "Starting cavasik-color-sync service..."
	systemctl --user start cavasik-color-sync.service
	@echo "Service started!"
	@sleep 1
	@make service-status

# Stop service
service-stop:
	@echo "Stopping cavasik-color-sync service..."
	systemctl --user stop cavasik-color-sync.service
	@echo "Service stopped!"

# Restart service
service-restart:
	@echo "Restarting cavasik-color-sync service..."
	systemctl --user restart cavasik-color-sync.service
	@echo "Service restarted!"
	@sleep 1
	@make service-status

# Check service status
service-status:
	@systemctl --user status cavasik-color-sync.service --no-pager || true

# View service logs
service-logs:
	journalctl --user -u cavasik-color-sync.service -f

# Clean temporary files
clean:
	@echo "Cleaning temporary files..."
	@rm -rf /tmp/cavasik-color-sync/
	@echo "Cache cleaned!"
	@echo "Note: Config file preserved at ~/.config/cavasik-color-sync/config.yaml"
