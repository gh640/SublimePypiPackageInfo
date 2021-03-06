# coding: utf-8

'''Provides a popup for Python PyPI packages.'''

import json
import os
import os.path
import sqlite3
import webbrowser
from abc import ABCMeta, abstractmethod
from datetime import datetime

import requests

import sublime
import sublime_plugin
import mdpopups


URL_JSON = 'https://pypi.org/pypi/{name}/json'
TEMPLATE = '''
# {name}

{summary}

- Page: [PyPI]({url_pypi}) / [Homepage]({url_homepage})
- Author: {author}

<div class="close-btn-wrapper">
    <a href="close">{btn_close}</a>
</div>
'''
CSS = '''
body {
    margin: 0;
    padding: 0;
}
.mdpopups {
}
.pypi-package-info {
    font-size: 12px;
    line-height: 20px;
    padding: 0 18px 10px 10px;
}
.pypi-package-info h1 {
    background-color: var(--mdpopups-admon-success-bg);
    color: var(--mdpopups-admon-success-title-fg);
    font-family: var(--mdpopups-font-mono);
    font-size: 12px;
    line-height: 12px;
    margin: 0 -18px 10px -10px;
    padding: 10px;
}
.pypi-package-info p {
    margin: 6px 0;
}
.pypi-package-info ul {
    margin: 6px 0;
}
.close-btn-wrapper {
    margin-top: 12px;
}
.close-btn-wrapper a {
    background-color: var(--mdpopups-admon-error-bg);
    color: var(--mdpopups-admon-error-fg);
    font-size: 10px;
    padding: 1px 6px;
    text-decoration: none;
}
'''
WRAPPER_CLASS = 'pypi-package-info'
MESSAGE_KEY = 'pypi_package_info'
MESSAGE_TTL = 4000
LENGTH_SUMMARY = 400
SETTINGS_KEY = 'PypiPackageInfo.sublime-settings'
CACHE_MAX_COUNT_DEFAULT = 1000


class FileFormat(metaclass=ABCMeta):
    '''Abstract class for file handler.'''

    @classmethod
    @abstractmethod
    def is_supported_file(cls, basename):
        pass

    @abstractmethod
    def is_focused(self, view, point):
        pass

    @abstractmethod
    def package_name(self, view, point):
        pass


class TomlFormat(FileFormat):
    '''Toml format handler.'''

    @classmethod
    def is_supported_file(cls, basename):
        return basename in ('pyproject.toml', 'Pipfile')

    def is_focused(self, view, point):
        return self._is_in_scope(view, point) and self._is_in_packages_table(
            view, point
        )

    def _is_in_scope(self, view, point):
        scope_name = view.scope_name(point)
        names = ('entity.name.tag.toml',)
        return all(n in scope_name for n in names)

    def _is_in_packages_table(self, view, point):
        packages_table_res = (
            # For `pyproject.toml` (Poerty).
            r'\[tool\.poetry\.dependencies\]',
            r'\[tool\.poetry\.dev-dependencies\]',
            # For `Pipenv`.
            r'^\[packages\]$',
            r'^\[dev-packages\]$',
        )
        table_re = r'^\[.+\]$'
        for package_table_re in packages_table_res:
            package_table = view.find(package_table_re, 0)
            if not package_table:
                continue

            region_begin = package_table.end()
            next_table = view.find(table_re, region_begin)
            if next_table:
                region_end = next_table.begin()
            else:
                region_end = view.size()

            if sublime.Region(region_begin, region_end).contains(point):
                return True

        return False

    def package_name(self, view, point):
        package_name = view.substr(view.extract_scope(point))
        return package_name.strip('"')


class RequirementsFormat(FileFormat):
    '''requirements.txt format handler.'''

    @classmethod
    def is_supported_file(cls, basename):
        return basename in ('requirements.txt',)

    def is_focused(self, view, point):
        return self._is_in_scope(view, point)

    def _is_in_scope(self, view, point):
        scope_name = view.scope_name(point)
        names = ('source.requirementstxt', 'string.package_name.requirementstxt')
        return all(n in scope_name for n in names)

    def package_name(self, view, point):
        # view.extract_scope() cannot be used here as it extracts too broad
        # region.
        region = view.expand_by_class(
            point, sublime.CLASS_WORD_START | sublime.CLASS_WORD_END
        )
        return view.substr(region)


class PypiPackageInfoPackageInfo(sublime_plugin.ViewEventListener):
    '''A view event listener for showing PyPI package data.'''

    formats = (TomlFormat, RequirementsFormat)

    def on_hover(self, point, hover_zone):
        if not self._is_on_text(hover_zone):
            return

        format_ = self._determine_format()
        if not format_:
            return

        if not format_.is_focused(self.view, point):
            return

        package_name = format_.package_name(self.view, point)

        show_status_message(self.view, 'Searching PyPI package data...')
        try:
            data_raw = self._fetch_package_info(package_name)
            data = self._extract_package_info(data_raw)
        except CustomBaseException as e:
            show_status_message(self.view, str(e))
            raise e
        else:
            self._show_popup(data, point)
            show_status_message(self.view, 'PyPI package data is found.')

    def on_popup_navigate(self, href):
        for url_prefix in ('https://', 'http://'):
            if href.startswith(url_prefix):
                webbrowser.open_new_tab(href)
                break

        mdpopups.hide_popup(self.view)

    def _determine_format(self):
        for klass in self.formats:
            if klass.is_supported_file(self._get_basename()):
                return klass()
        return None

    def _get_basename(self):
        file_name = self.view.file_name()
        return os.path.basename(file_name) if file_name else ''

    def _is_on_text(self, hover_zone):
        return hover_zone == sublime.HOVER_TEXT

    def _fetch_package_info(self, name):
        return PackageDataManager().get_data(name)

    def _extract_package_info(self, data):
        try:
            info = data['info']
            summary = self._truncate(info['summary'], LENGTH_SUMMARY)
            return {
                'name': info['name'],
                'summary': summary,
                'url_pypi': info['package_url'],
                'url_homepage': info['home_page'],
                'author': info['author'],
                'btn_close': chr(0x00D7),
            }
        except Exception as e:
            raise CustomBaseException(
                'Package data extraction failed for "{}".'.format(data)
            )

    def _show_popup(self, data, location):
        if mdpopups.is_popup_visible(self.view):
            mdpopups.hide_popup(self.view)

        mdpopups.show_popup(
            self.view,
            TEMPLATE.format(**data),
            css=CSS,
            wrapper_class=WRAPPER_CLASS,
            max_width=400,
            location=location,
            flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
            on_navigate=self.on_popup_navigate,
        )

    def _truncate(self, string, count):
        ellipsis = '...'
        if len(string) > count:
            return string[: count - len(ellipsis)] + ellipsis
        else:
            return string


class PypiPackageInfoClearAllCacheCommand(sublime_plugin.ApplicationCommand):
    '''Application command named pypi_package_info_clear_all_cache.'''

    def run(self):
        cache = PackageCache()
        cache.clear_all_cache()
        view = sublime.active_window().active_view()
        show_status_message(view, 'PyPI package info cache cleared.')


class PackageDataManager:
    '''Package data manager.'''

    def get_data(self, name):
        cache = PackageCache()
        package_data = cache.get_package_data(name)
        if not package_data:
            package_data = self._fetch_data(name)
            cache.add_package_data(name, package_data)
        return package_data

    def _fetch_data(self, name):
        response = requests.get(URL_JSON.format(name=name))
        if not response.ok:
            raise CustomBaseException(
                'Package data fetch failed for "{}".'.format(name)
            )
        return response.json()


class PackageCache:
    '''Package cache manager.'''

    def __init__(self):
        self.conn = sqlite3.connect(self._get_path())
        self.conn.row_factory = sqlite3.Row
        self._create_table_if_not_exists()

    def __del__(self):
        self.conn.close()

    def get_package_data(self, name):
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM packages WHERE name=?', (name,))
        row = cur.fetchone()
        if row:
            cur.execute(
                'UPDATE packages SET updated_at=? WHERE name=?', (get_now(), name)
            )
            self.conn.commit()
            cur.close()
            data = row['data']
            return json.loads(data)

        return False

    def add_package_data(self, name, data):
        row = (name, json.dumps(data), get_now())
        cur = self.conn.cursor()
        cur.execute('INSERT INTO packages VALUES (?, ?, ?)', row)
        self.conn.commit()
        cur.close()
        self.clear_old_cache()

    def clear_old_cache(self):
        cache_max_count = self._get_cache_max_count()
        if cache_max_count > 0:
            cur = self.conn.cursor()
            cur.execute('SELECT COUNT(*) FROM packages')
            count = cur.fetchone()[0]
            if count > cache_max_count:
                cur.execute(
                    '''
                    DELETE FROM packages WHERE name NOT IN (
                        SELECT name FROM packages
                            ORDER BY updated_at DESC LIMIT ?
                    )
                    ''',
                    (cache_max_count,),
                )
                self.conn.commit()
            cur.close()

    def clear_all_cache(self):
        self.conn.close()
        os.remove(self._get_path())

    def _get_path(self):
        cache_manager = CacheManager()
        cache_manager.create_directory()
        return cache_manager.get_path('cache.sqlite3')

    def _create_table_if_not_exists(self):
        self.conn.execute(
            '''
            CREATE TABLE IF NOT EXISTS packages
                (name text, data blob, updated_at integer)
            '''
        )

    def _get_cache_max_count(self):
        settings = sublime.load_settings(SETTINGS_KEY)
        max_count = settings.get('cache_max_count', CACHE_MAX_COUNT_DEFAULT)
        try:
            return int(max_count)
        except ValueError as e:
            print(
                '`cache_max_count` must be an integer. '
                'The value is set to "{!r}". '
                'The default value {} is used instead.'.format(
                    max_count, CACHE_MAX_COUNT_DEFAULT
                )
            )
            return CACHE_MAX_COUNT_DEFAULT


class CacheManager:
    '''Cache manager for Sublime Text cache system.'''

    def get_path(self, name):
        return os.path.join(self._get_directory_path(), name)

    def create_directory(self):
        directory = self._get_directory_path()
        if not os.path.isdir(directory):
            os.mkdir(directory, mode=0o700)

    def _get_directory_path(self):
        return os.path.join(sublime.cache_path(), __package__)


def show_status_message(view, message):
    '''Shows a temporary status message.'''
    view.set_status(MESSAGE_KEY, message)
    sublime.set_timeout(lambda: view.erase_status(MESSAGE_KEY), MESSAGE_TTL)


def get_now():
    '''Gets the current timestamp.'''
    return int(datetime.now().timestamp())


class CustomBaseException(Exception):
    '''Base exception class for this package.'''

    pass
