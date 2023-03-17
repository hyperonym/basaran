NAME := basaran
VERSION := 0.12.0

DOCKER_HUB_OWNER ?= hyperonym
DOCKER_HUB_IMAGE := $(DOCKER_HUB_OWNER)/$(NAME):$(VERSION)

GITHUB_PACKAGES_OWNER ?= hyperonym
GITHUB_PACKAGES_IMAGE := ghcr.io/$(GITHUB_PACKAGES_OWNER)/$(NAME):$(VERSION)

.PHONY: changelog
changelog:
	@mkdir -p dist
	@git log $(shell git describe --tags --abbrev=0 2> /dev/null)..HEAD --pretty='tformat:* [%h] %s' > dist/changelog.md
	@cat dist/changelog.md

.PHONY: clean
clean:
	@find . -type f -name "*.py[co]" -delete && find . -type d -name "__pycache__" -delete
	@rm -rf dist/ .pytest_cache/ htmlcov/ .coverage

.PHONY: docker-hub
docker-hub:
	@docker buildx build --push --tag $(DOCKER_HUB_IMAGE) .

.PHONY: github-packages
github-packages:
	@docker buildx build --push --tag $(GITHUB_PACKAGES_IMAGE) .

.PHONY: github-release
github-release: changelog
	@gh release create v$(VERSION) -F dist/changelog.md -t v$(VERSION)

.PHONY: lint
lint:
	@flake8 basaran/ --count --select=E9,F63,F7,F82 --show-source --statistics
	@flake8 basaran/ --count --exit-zero --max-complexity=10 --max-line-length=80 --statistics

.PHONY: test
test:
	@python -m pytest

.PHONY: test-coverage
test-coverage:
	@coverage run -m pytest
	@coverage report
