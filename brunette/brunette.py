#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from pathspec import PathSpec
from typing import (
    List,
    Optional,
    Pattern,
    Set,
    Tuple,
    Iterator,
)

import black
import click
from black import (
    DEFAULT_LINE_LENGTH,
    TargetVersion,
    DEFAULT_INCLUDES,
    DEFAULT_EXCLUDES,
    WriteBack,
    FileMode,
    re_compile_maybe_verbose,
    Report,
    find_project_root,
    path_empty,
    __version__,
    out,
    Path,
    get_gitignore,
    err,
    format_str,
    PY36_VERSIONS,
)
import configparser


def gen_python_files_in_dir(
    path: Path,
    root: Path,
    include: Pattern[str],
    exclude: Pattern[str],
    report: 'Report',
    gitignore: PathSpec,
) -> Iterator[Path]:
    """Generate all files under `path` whose paths are not excluded by the
    `exclude` regex, but are included by the `include` regex.

    Symbolic links pointing outside of the `root` directory are ignored.

    `report` is where output about exclusions goes.
    """
    for child in path.iterdir():
        # First ignore files matching .gitignore
        if gitignore.match_file(child.as_posix()):
            report.path_ignored(child, 'matches the .gitignore file content')
            continue

        # Then ignore with `exclude` option.
        try:
            normalized_path = (
                '/' + child.resolve().relative_to(root).as_posix()
            )
        except OSError as e:
            report.path_ignored(child, f'cannot be read because {e}')
            continue

        except ValueError:
            if child.is_symlink():
                report.path_ignored(
                    child, f'is a symbolic link that points outside {root}'
                )
                continue

            raise

        if child.is_dir():
            normalized_path += '/'

        exclude_match = exclude.search(normalized_path)
        if exclude_match and exclude_match.group(0):
            report.path_ignored(
                child, 'matches the --exclude regular expression'
            )
            continue

        if child.is_dir():
            yield from gen_python_files_in_dir(
                child, root, include, exclude, report, gitignore
            )

        elif child.is_file():
            include_match = include.search(normalized_path)
            if include_match:
                yield child


def patched_normalize_string_quotes(leaf: black.Leaf) -> None:
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


def reformat_many(sources, *args, **kwargs):
    """Monkeypatched to reformat multiple files using ``black.reformat_one``."""
    for src in sources:
        black.reformat_one(src, *args, **kwargs)


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option(
    '-c', '--code', type=str, help='Format the code passed in as a string.'
)
@click.option(
    '-l',
    '--line-length',
    type=int,
    default=DEFAULT_LINE_LENGTH,
    help='How many characters per line to allow.',
    show_default=True,
)
@click.option(
    '-t',
    '--target-version',
    type=click.Choice([v.name.lower() for v in TargetVersion]),
    callback=lambda c, p, v: [TargetVersion[val.upper()] for val in v],
    multiple=True,
    help=(
        "Python versions that should be supported by Black's output. [default: "
        'per-file auto-detection]'
    ),
)
@click.option(
    '--py36',
    is_flag=True,
    help=(
        'Allow using Python 3.6-only syntax on all input files.  This will put '
        'trailing commas in function signatures and calls also after *args and '
        '**kwargs. Deprecated; use --target-version instead. '
        '[default: per-file auto-detection]'
    ),
)
@click.option(
    '--pyi',
    is_flag=True,
    help=(
        'Format all input files like typing stubs regardless of file extension '
        '(useful when piping source on standard input).'
    ),
)
@click.option(
    '-S',
    '--skip-string-normalization',
    is_flag=True,
    help="Don't normalize string quotes or prefixes.",
)
@click.option(
    '-sq',
    '--single-quotes',
    is_flag=True,
    help="Prefer SINGLE quotes if it doesn't cause more escaping.",
)
@click.option(
    '--check',
    is_flag=True,
    help=(
        "Don't write the files back, just return the status.  Return code 0 "
        'means nothing would change.  Return code 1 means some files would be '
        'reformatted.  Return code 123 means there was an internal error.'
    ),
)
@click.option(
    '--diff',
    is_flag=True,
    help="Don't write the files back, just output a diff for each file on stdout.",
)
@click.option(
    '--fast/--safe',
    is_flag=True,
    help='If --fast given, skip temporary sanity checks. [default: --safe]',
)
@click.option(
    '--include',
    type=str,
    default=DEFAULT_INCLUDES,
    help=(
        'A regular expression that matches files and directories that should be '
        'included on recursive searches.  An empty value means all files are '
        'included regardless of the name.  Use forward slashes for directories on '
        'all platforms (Windows, too).  Exclusions are calculated first, inclusions '
        'later.'
    ),
    show_default=True,
)
@click.option(
    '--exclude',
    type=str,
    default=DEFAULT_EXCLUDES,
    help=(
        'A regular expression that matches files and directories that should be '
        'excluded on recursive searches.  An empty value means no paths are excluded. '
        'Use forward slashes for directories on all platforms (Windows, too).  '
        'Exclusions are calculated first, inclusions later.'
    ),
    show_default=True,
)
@click.option(
    '-q',
    '--quiet',
    is_flag=True,
    help=(
        "Don't emit non-error messages to stderr. Errors are still emitted; "
        'silence those with 2>/dev/null.'
    ),
)
@click.option(
    '-v',
    '--verbose',
    is_flag=True,
    help=(
        'Also emit messages to stderr about files that were not changed or were '
        'ignored due to --exclude=.'
    ),
)
@click.version_option(version=__version__)
@click.argument(
    'src',
    nargs=-1,
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=True,
        readable=True,
        allow_dash=True,
    ),
    is_eager=True,
)
@click.option(
    '--config',
    type=click.Path(
        exists=False,
        file_okay=True,
        dir_okay=False,
        readable=True,
        allow_dash=False,
    ),
    is_eager=True,
    callback=read_config_file,
    help='Read configuration from PATH.',
)
@click.pass_context
def main(
    ctx: click.Context,
    code: Optional[str],
    line_length: int,
    target_version: List[TargetVersion],
    check: bool,
    diff: bool,
    fast: bool,
    pyi: bool,
    py36: bool,
    skip_string_normalization: bool,
    single_quotes: bool,
    quiet: bool,
    verbose: bool,
    include: str,
    exclude: str,
    src: Tuple[str],
    config: Optional[str],
) -> None:
    """The uncompromising code formatter."""
    write_back = WriteBack.from_configuration(check=check, diff=diff)
    if target_version:
        if py36:
            err('Cannot use both --target-version and --py36')
            ctx.exit(2)
        else:
            versions = set(target_version)
    elif py36:
        err(
            '--py36 is deprecated and will be removed in a future version. '
            'Use --target-version py36 instead.'
        )
        versions = PY36_VERSIONS
    else:
        # We'll autodetect later.
        versions = set()
    mode = FileMode(
        target_versions=versions,
        line_length=line_length,
        is_pyi=pyi,
        string_normalization=not skip_string_normalization,
    )

    if single_quotes:
        black.normalize_string_quotes = patched_normalize_string_quotes

    if config and verbose:
        out(f'Using configuration from {config}.', bold=False, fg='blue')
    if code is not None:
        print(format_str(code, mode=mode))
        ctx.exit(0)
    try:
        include_regex = re_compile_maybe_verbose(include)
    except re.error:
        err(f'Invalid regular expression for include given: {include!r}')
        ctx.exit(2)
    try:
        exclude_regex = re_compile_maybe_verbose(exclude)
    except re.error:
        err(f'Invalid regular expression for exclude given: {exclude!r}')
        ctx.exit(2)
    report = Report(check=check, quiet=quiet, verbose=verbose)
    root = find_project_root(src)
    sources: Set[Path] = set()
    path_empty(src=src, quiet=quiet, verbose=verbose, ctx=ctx, msg=None)
    for s in src:
        p = Path(s)
        if p.is_dir():
            sources.update(
                gen_python_files_in_dir(
                    p,
                    root,
                    include_regex,
                    exclude_regex,
                    report,
                    get_gitignore(root),
                )
            )
        elif p.is_file() or s == '-':
            # if a file was explicitly given, we don't care about its extension
            sources.add(p)
        else:
            err(f'invalid path: {s}')
    if len(sources) == 0:
        if verbose or not quiet:
            out('No Python files are present to be formatted. Nothing to do 😴')
        ctx.exit(0)

    reformat_many(
        sources=sources,
        fast=fast,
        write_back=write_back,
        mode=mode,
        report=report,
    )

    if verbose or not quiet:
        out('Oh no! 💥 💔 💥' if report.return_code else 'All done! ✨ 🍰 ✨')
        click.secho(str(report), err=True)
    ctx.exit(report.return_code)


def cli_main():
    main()


if __name__ == '__main__':
    cli_main()
