# PypiPackageInfo

A Sublime Text 3 package which provides a popup for Python PyPI packages in Pipfile.

![capture](https://raw.githubusercontent.com/gh640/SublimePypiPackageInfo/master/assets/capture.png)

## Requirements

- [TOML](https://packagecontrol.io/packages/TOML): A Sublime Text package for TOML syntax.
    - `PypiPackageInfo` uses TOML syntax to detect if the pointed scope is a package name.

## Installation

Install the pacakge.

1. Install [Package Control](https://packagecontrol.io/installation) to your Sublime Text 3.
2. Open the command palette and select `Package Controll: Install Package`.
3. Search for and select `PypiPackageInfo`.

Then, install `TOML` syntax if it has not been installed.

1. Open the command palette and select `Package Controll: Install Package`.
2. Search for and select `TOML`.

Select `TOML` as a syntax for all `Pipfile`s.

`User/TOML.sublime-settings`:

```json
{
  "extensions":
  [
    "Pipfile"
  ]
}
```

## Usage

![capture](https://raw.githubusercontent.com/gh640/SublimePypiPackageInfo/master/assets/capture.gif)

Hover the cursor on a package name in your `Pipfile` and the package information is fetched and shown in a popup window.

Currently only `Pipfile` files are supported and no other formats like `requirements.txt` are supported.

## Links

- [`ComposerPackageInfo`](https://packagecontrol.io/packages/ComposerPackageInfo): `PypiPackageInfo` uses the same logic as one `ComposerPackageInfo` uses.

## License

Licensed under MIT License.
