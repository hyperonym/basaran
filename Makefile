NAME := basaran
VERSION := 0.3.1

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
	@rm -rf dist/

.PHONY: docker-hub
docker-hub:
	@docker buildx build --push --tag $(DOCKER_HUB_IMAGE) .

.PHONY: github-packages
github-packages:
	@docker buildx build --push --tag $(GITHUB_PACKAGES_IMAGE) .

.PHONY: github-release
github-release: changelog
	@gh release create v$(VERSION) -F dist/changelog.md -t v$(VERSION)
