"""Helper function for extracting bitcode with gllvm."""
import argparse
import os
import shutil
import subprocess
import sys

from pathlib import Path
from typing import Dict


def eprint(*args):
    """Error print"""
    print(*args, file=sys.stderr)


def run(message, cmd, **kwargs):
    """Print and execute a command."""
    env_fmt = ''
    if 'env' in kwargs:
        env_diff = set(kwargs['env'].items()) - set(os.environ.items())
        env_fmt = ' '.join([f"{key}='{val}'" for key, val in env_diff])
    eprint(message + ':', env_fmt, ' '.join([f"'{x}'" for x in cmd]))
    subprocess.run(cmd, check=True, **kwargs)


class Builder:
    """Represent a common building process."""

    def __init__(self,
                 with_install_dir=False,
                 with_cmake=False,
                 with_make=False,
                 with_gclang=False,
                 with_target=False,
                 in_source_build=False):
        parser = argparse.ArgumentParser(description=self.__doc__)
        parser.add_argument('--build-dir',
                            help='Directory for the building.',
                            required=True,
                            type=Path)
        parser.add_argument('--src-dir',
                            help='Directory for the programs sourcecode.',
                            required=True,
                            type=Path)
        parser.add_argument('--get-bc-program',
                            help='get-bc executable.',
                            required=True,
                            type=Path)
        parser.add_argument('--llvm-objcopy-program',
                            help='llvm-objcopy executable.',
                            required=True,
                            type=Path)
        parser.add_argument('--llvm-ld-program',
                            help='lld executable.',
                            required=True,
                            type=Path)
        parser.add_argument('--output',
                            help='Bitcode output file.',
                            required=True,
                            type=Path)
        parser.add_argument('--llvm-bindir',
                            help='Directory that contains the LLVM tools.',
                            required=True,
                            type=Path)

        if with_gclang:
            parser.add_argument('--gclang-program',
                                help='gclang executable.',
                                required=True,
                                type=Path)

        if with_target:
            parser.add_argument('--target',
                                help='Ninja or make target.',
                                required=True,
                                type=Path)

        if with_install_dir:
            parser.add_argument('--install-dir',
                                help='Directory for the local installation.',
                                required=True,
                                type=Path)

        if in_source_build:
            parser.add_argument('--meson-build-dir',
                                help='Directory for the meson build directory',
                                required=True,
                                type=Path)

        if with_cmake:
            parser.add_argument('--cmake-args',
                                help='CMake arguments (given as "foo=bar")',
                                required=True,
                                nargs='*')
            parser.add_argument('--cmake-program',
                                help='CMake executable.',
                                required=True,
                                type=Path)
            parser.add_argument('--ninja-program',
                                help='Ninja executable.',
                                required=True,
                                type=Path)

        if with_make:
            parser.add_argument('--make-program',
                                help='Make executable.',
                                required=True,
                                type=Path)
            parser.add_argument('--make-args',
                                help='Make arguments',
                                nargs='*')
            parser.add_argument('--jobs',
                                help='Run Make with that many jobs.',
                                type=int)

        self.args = parser.parse_args()

        def check(arg, what):
            func = getattr(arg, what)
            assert func(), f"{arg} not {what}"

        check(self.args.src_dir, "is_dir")
        check(self.args.get_bc_program, "is_file")
        check(self.args.llvm_objcopy_program, "is_file")
        check(self.args.llvm_ld_program, "is_file")
        check(self.args.llvm_bindir, "is_dir")

        if with_cmake:
            assert self.args.cmake_program.is_file()
            assert self.args.ninja_program.is_file()

        if with_gclang:
            assert self.args.gclang_program.is_file()

        if with_make:
            assert self.args.make_program.is_file()
            if self.args.jobs:
                self.jobs = self.args.jobs
            else:
                self.jobs = len(os.sched_getaffinity(0))

        self.in_source = False
        if in_source_build:
            assert self.args.meson_build_dir.is_dir()
            self.in_source = True

    def _make_new(self, s_dir: Path):
        if s_dir.is_dir():
            shutil.rmtree(s_dir)
        s_dir.mkdir()

    def _copy_src(self):
        """Copy all sources to the build directory for in-source builds."""
        if self.args.build_dir.is_dir():
            shutil.rmtree(self.args.build_dir)

        def ignore(dir, ins):
            ignores = ['.git']
            if not self.in_source:
                return ignores

            for name in ins:
                if Path(dir, name) == self.args.meson_build_dir:
                    ignores.append(name)
                if name == 'subprojects' and Path(dir) == self.args.src_dir:
                    ignores.append('subprojects')
            return ignores

        shutil.copytree(self.args.src_dir, self.args.build_dir, ignore=ignore)

    def _get_gllvm_env(self):
        env = {**os.environ}
        env['LLVM_COMPILER_PATH'] = str(self.args.llvm_bindir.absolute())
        env['GLLVM_OBJCOPY'] = str(self.args.llvm_objcopy_program.absolute())
        env['GLLVM_LD'] = str(self.args.llvm_ld_program.absolute())
        # cmake_env['WLLVM_OUTPUT_LEVEL'] = 'DEBUG'
        return env

    def _get_bc(self, image: Path, env: Dict[str, str]):
        get_bc_cmd = [
            self.args.get_bc_program, '-o',
            self.args.output.absolute(),
            image.absolute()
        ]
        run('Executing get-bc', get_bc_cmd, cwd=self.args.build_dir, env=env)

    def do_build(self):
        """Trigger the actual build process."""
        raise NotImplementedError()
