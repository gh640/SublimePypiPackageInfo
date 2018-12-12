# PypiPackageInfo

A Sublime Text 3 package which provides a popup for Python PyPI packages in `pyproject.toml`/`Pipfile`.

![capture](https://raw.githubusercontent.com/gh640/SublimePypiPackageInfo/master/assets/capture.png)

## Supported files

The following files are supported.

- `pyproject.toml` (Poetry)
- `Pipfile` (Pipenv)

## Requirements

- [TOML](https://packagecontrol.io/packages/TOML): A Sublime Text package for TOML syntax.
    - `PypiPackageInfo` uses TOML syntax to detect if the pointed scope is a package name.

## Installation

Install the package.

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

### Displaying package information popup

![capture](https://raw.githubusercontent.com/gh640/SublimePypiPackageInfo/master/assets/capture.gif)

Hover the cursor on a package name in your `pyproject.toml`/`Pipfile` and the package information is fetched and shown in a popup window.

Currently only `pyproject.toml`/`Pipfile` files are supported and no other formats like `requirements.txt` are supported.

### Clearing local cache

Fetched package data are stored in the local SQLite database `cache.sqlite3` in the Sublime Text's cache directory. You can delete all the cache with the command `PypiPackageInfo: Clear all cache`.

1. Open the command palette.
2. Search and select `ComposerPackageInfo: Clear all cache`.
3. The cache data are deleted.

## Settings

There are following setting options.

- `cache_max_count`

`cache_max_count`
:    (default: `1000`) Max number of locally cached package data. If the number of cached package data gets greater than this value, old tuples are deleted from the database table.

You can edit the setting file via Menu → Preferences → Package Settings → PypiPackageInfo → Settings .

## Links

- [`ComposerPackageInfo`](https://packagecontrol.io/packages/ComposerPackageInfo): `PypiPackageInfo` uses the same logic as one `ComposerPackageInfo` uses.
- [`pipenv-sublime`](https://github.com/kennethreitz/pipenv-sublime): A Sublime Text pugin for handling projects with Pipenv.
- [Poetry: Dependency Management for Python](https://github.com/sdispater/poetry)

## License

Licensed under the MIT License.
