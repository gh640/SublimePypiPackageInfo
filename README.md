# PypiPackageInfo

A Sublime Text 3 package which provides a popup for Python PyPI packages in Pipfile.

## Requirements

- [TOML](https://packagecontrol.io/packages/TOML): A Sublime Text package for TOML syntax.
    - `PypiPackageInfo` uses TOML syntax to detect if the pointed scope is a package name.

## Installation

...

## Usage

Hover the cursor on a package name in your `Pipfile` and the package information is fetched and shown in a popup window.

Currently only `Pipfile` files are supported and no other formats like `requirements.txt` are supported.

## Link

- [`ComposerPackageInfo`](https://packagecontrol.io/packages/ComposerPackageInfo): `PypiPackageInfo` uses the same logic as one `ComposerPackageInfo` uses.

## License

Licensed under MIT License.
