# Makefile for TSP Genetic Algorithm Project

# Compiler settings
CC        := gcc
CFLAGS    := -O3 -ffast-math -std=c99
DEBUG_FLAGS := -g -DDEBUG -O0 -Wall -Wextra
LIBS      := -lm

# Source file
SRC = GA_TSP_Serial_Random.c

# Executable name
EXEC = gatsp

# Directories
INSTANCES_DIR = instances
RESULTS_DIR = results

# Default target
all: $(EXEC)

# Build the executable
$(EXEC): $(SRC)
	@echo "Building TSP Genetic Algorithm..."
	$(CC) $(CFLAGS) -o $@ $< $(LIBS)
	@echo "Build complete! Executable: ./$(EXEC)"

# Debug build
debug: CFLAGS += $(DEBUG_FLAGS)
debug: clean $(EXEC)
	@echo "Debug version built with symbols"

# Create necessary directories
dirs:
	@mkdir -p $(INSTANCES_DIR) $(RESULTS_DIR)
	@echo "Created directories: $(INSTANCES_DIR), $(RESULTS_DIR)"

# Test targets
test-random: $(EXEC)
	@echo "=== Testing Random Mode ==="
	./$(EXEC)

test-instance: $(EXEC)
	@echo "=== Testing Instance Mode ==="
	./$(EXEC) instance_mode

test-both: test-random test-instance

# Clean targets
clean:
	rm -f $(EXEC)
	rm -f *.o core
	@echo "Cleaned executable and object files"

clean-results:
	rm -rf $(RESULTS_DIR)/*
	@echo "Cleaned results directory"

clean-all: clean clean-results
	@echo "Full cleanup completed"

# Install target
install: $(EXEC)
	@echo "Installing $(EXEC) to /usr/local/bin..."
	sudo cp $(EXEC) /usr/local/bin/
	@echo "Installation complete"

uninstall:
	@echo "Removing $(EXEC) from /usr/local/bin..."
	sudo rm -f /usr/local/bin/$(EXEC)
	@echo "Uninstallation complete"

# Help
help:
	@echo "=== TSP Genetic Algorithm Makefile ==="
	@echo ""
	@echo "BUILD TARGETS:"
	@echo "  all          - Build the executable (default)"
	@echo "  debug        - Build debug version"
	@echo ""
	@echo "TEST TARGETS:"
	@echo "  test-random  - Run in random mode"
	@echo "  test-instance- Run in instance mode"
	@echo "  test-both    - Run both modes"
	@echo ""
	@echo "UTILITY TARGETS:"
	@echo "  dirs         - Create necessary directories"
	@echo "  clean        - Remove executable"
	@echo "  clean-all    - Remove executable and results"
	@echo "  install      - Install to /usr/local/bin"
	@echo "  uninstall    - Remove from /usr/local/bin"
	@echo ""
	@echo "USAGE:"
	@echo "  make                    # Build executable"
	@echo "  make test-random        # Test random mode"
	@echo "  make test-instance      # Test instance mode"
	@echo "  ./gatsp                 # Run random mode"
	@echo "  ./gatsp instance_mode   # Run instance mode"

# Phony targets
.PHONY: all debug dirs test-random test-instance test-both clean clean-results clean-all install uninstall help

# Default goal
.DEFAULT_GOAL := all