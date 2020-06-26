#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import black
import configparser


def normalize_string_quotes(leaf: black.Leaf) -> None:
    """
    Prefer SINGLE quotes but only if it doesn't cause more escaping.
    Prefer double quotes for docstrings.

    Adds or removes backslashes as appropriate. Doesn't parse and fix
    strings nested in f-strings (yet).

    Note: Mutates its argument.
    """
    single_quotes = True
    preferred_quote = "'" if single_quotes else '"'
    other_quote = '"' if single_quotes else "'"

    value = leaf.value.lstrip('furbFURB')
    if value[:3] == '"""':
        return

    elif value[:3] == "'''":
        orig_quote = "'''"
        new_quote = '"""'
    elif value[0] == preferred_quote:
        orig_quote = preferred_quote
        new_quote = other_quote
    else:
        orig_quote = other_quote
        new_quote = preferred_quote
    first_quote_pos = leaf.value.find(orig_quote)
    if first_quote_pos == -1:
        return  # There's an internal error

    prefix = leaf.value[:first_quote_pos]
    unescaped_new_quote = re.compile(rf'(([^\\]|^)(\\\\)*){new_quote}')
    escaped_new_quote = re.compile(rf'([^\\]|^)\\((?:\\\\)*){new_quote}')
    escaped_orig_quote = re.compile(rf'([^\\]|^)\\((?:\\\\)*){orig_quote}')
    body = leaf.value[first_quote_pos + len(orig_quote) : -len(orig_quote)]
    if 'r' in prefix.casefold():
        if unescaped_new_quote.search(body):
            # There's at least one unescaped new_quote in this raw string
            # so converting is impossible
            return
        # Do not introduce or remove backslashes in raw strings
        new_body = body
    else:
        # remove unnecessary escapes
        new_body = black.sub_twice(
            escaped_new_quote, rf'\1\2{new_quote}', body
        )
        if body != new_body:
            # Consider the string without unnecessary escapes as the original
            body = new_body
            leaf.value = f'{prefix}{orig_quote}{body}{orig_quote}'
        new_body = black.sub_twice(
            escaped_orig_quote, rf'\1\2{orig_quote}', new_body
        )
        new_body = black.sub_twice(
            unescaped_new_quote, rf'\1\\{new_quote}', new_body
        )
    if 'f' in prefix.casefold():
        matches = re.findall(
            r"""
            (?:[^{]|^)\{  # start of the string or a non-{ followed by a single {
                ([^{].*?)  # contents of the brackets except if begins with {{
            \}(?:[^}]|$)  # A } followed by end of the string or a non-}
            """,
            new_body,
            re.VERBOSE,
        )
        for m in matches:
            if '\\' in str(m):
                # Do not introduce backslashes in interpolated expressions
                return

    if new_quote == '"""' and new_body[-1:] == '"':
        # edge case:
        new_body = new_body[:-1] + '\\"'
    orig_escape_count = body.count('\\')
    new_escape_count = new_body.count('\\')
    if new_escape_count > orig_escape_count:
        return  # Do not introduce more escaping

    if new_escape_count == orig_escape_count and orig_quote == preferred_quote:
        return

    leaf.value = f'{prefix}{new_quote}{new_body}{new_quote}'


def read_config_file(ctx, param, value):
    if not value:
        root = black.find_project_root(ctx.params.get('src', ()))
        path = root / 'setup.cfg'
        if path.is_file():
            value = str(path)
        else:
            return None

    config = configparser.ConfigParser()
    config.read(value)
    try:
        config = dict(config['tool:brunette'])
    except KeyError:
        return None
    if not config:
        return None

    try:
        if configparser.ConfigParser.BOOLEAN_STATES[
            config['single-quotes'].lower()
        ]:
            black.normalize_string_quotes = normalize_string_quotes
        del config['single-quotes']
    except KeyError:
        pass

    if ctx.default_map is None:
        ctx.default_map = {}

    for k, v in config.items():
        k = k.replace('--', '').replace('-', '_')
        for command_param in ctx.command.params:
            if command_param.name == k:
                if command_param.multiple:
                    v = v.split(',')
                break
        else:
            raise KeyError('Invalid paramater: {}'.format(k))

        ctx.default_map[k] = v

    return value


BLACK_MAIN = black.main


def main():
    config_file_opt = [p for p in BLACK_MAIN.params if p.name == 'config'][0]
    config_file_opt.callback = read_config_file
    options = [p for p in BLACK_MAIN.params if p.name != 'config']
    options.append(config_file_opt)
    BLACK_MAIN.params = options
    return BLACK_MAIN()


def cli_main():
    black.main = main
    black.patched_main()


if __name__ == '__main__':
    cli_main()
