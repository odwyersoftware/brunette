import os
import tempfile
import subprocess
import importlib.util

import pytest

NAME = 'brunette'
SINGLE_QUOTES = 'single-quotes'
SINGLE_QUOTES_OP = '--' + SINGLE_QUOTES
THIS_DIR = os.path.abspath(os.path.dirname(__file__))


class Test:
    @pytest.fixture(autouse=True)
    def setup(self):
        # Try making sure we test on dev!
        self._dev = os.path.normcase(
            os.path.join(os.path.dirname(THIS_DIR), NAME)
        )

        try:
            origin = importlib.util.find_spec(NAME).origin
        except AttributeError:
            raise RuntimeError(
                f'{NAME} is not installed!\n'
                'In your dev repo root run:\n\n  '
                'pip install -e .\n\n'
            )

        self._origin = os.path.normcase(os.path.dirname(origin))

        if self._dev != self._origin:
            raise RuntimeError(
                f'This is not testing the local dev version of {NAME}!\n'
                f'  local: {self._dev}\n  origin: {self._origin}\n'
                'In your dev repo root run:\n\n'
                f'  pip uninstall -y {NAME}\n  pip install -e .\n\n'
            )

    def test_single_quotes(self):
        test_code = _get_demo_content('string_quotes_in')
        expected_single = _lines(_get_demo_content('string_quotes_out_single'))
        results_single = _get_result_lines(
            [NAME, SINGLE_QUOTES_OP, '--code', test_code]
        )

        for result, expected in zip(results_single, expected_single):
            assert result == expected

    def test_default_quotes(self):
        test_code = _get_demo_content('string_quotes_in')
        expected_def = _lines(_get_demo_content('string_quotes_out_default'))
        results_default = _get_result_lines([NAME, '--code', test_code])

        for result, expected in zip(results_default, expected_def):
            assert result == expected

    def test_config_default_quotes(self):
        test_code = _get_demo_content('string_quotes_in')
        expected_def = _lines(_get_demo_content('string_quotes_out_default'))

        handle, config_path = tempfile.mkstemp()
        with open(handle, 'w') as file_obj:
            file_obj.write(f'[tool:{NAME}]\n{SINGLE_QUOTES} = false')

        results_default = _get_result_lines(
            [NAME, f'--config={config_path}', '--code', test_code]
        )
        for result, expected in zip(results_default, expected_def):
            assert result == expected

        os.unlink(config_path)

    def test_config_default_single(self):
        test_code = _get_demo_content('string_quotes_in')
        expected_single = _lines(_get_demo_content('string_quotes_out_single'))

        handle, config_path = tempfile.mkstemp()
        with open(handle, 'w') as file_obj:
            file_obj.write(f'[tool:{NAME}]\n{SINGLE_QUOTES} = true')

        results_default = _get_result_lines(
            [NAME, f'--config={config_path}', '--code', test_code]
        )
        for result, expected in zip(results_default, expected_single):
            assert result == expected

        os.unlink(config_path)


def _get_result_lines(args):
    return _lines(subprocess.check_output(args, encoding='utf8'))


def _lines(text: str):
    """Fix escaped linebreaks then split."""
    return text.strip().replace('\\n\\\n', '\\n').split('\n')


def _get_demo_content(file_name: str):
    """Get data file content inline."""
    path = os.path.join(THIS_DIR, 'data', file_name + '.py')
    with open(path) as file_obj:
        return file_obj.read()
