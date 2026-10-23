.PHONY: check test package clean

check:  ## Validate skill format and marketplace paths
	python3 tools/check_skill.py

test:   ## Run script tests against the eval fixtures
	python3 -m unittest discover -s tests -v

package: check  ## Build dist/health-breach-watch.zip for the Claude app
	python3 tools/package.py

clean:
	rm -rf dist
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
