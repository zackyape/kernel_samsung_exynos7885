from argparse import ArgumentParser
from pathlib import Path
from datetime import datetime
import os
import shutil
import subprocess
from typing import Optional

from .utils import check_file, print_dictinfo, match_and_get, zip_files
from .popen_impl import popen_impl
from .compiler import CompilerClang, CompilerGCC
from .loginit import logging


class KernelBuild:
    def __init__(
        self,
        name: str,
        arch: str,
        kernelType: str,
        anykernelDir: Optional[Path] = None,
        toolchainDir: Optional[Path] = None,
        outDir: Optional[Path] = None,
    ):
        self.kernel_name = name
        self.toolchainDir = toolchainDir if toolchainDir else Path("toolchain")
        self.outDir = outDir if outDir else Path("out")
        self.anykernelDir = anykernelDir
        self.arch = arch
        self.kernelType = kernelType

    def initArgParser(self) -> ArgumentParser:
        argparser = ArgumentParser(
            description=f"Build {self.kernel_name} with specified arguments"
        )
        argparser.add_argument(
            "--allow-dirty", action="store_true", help="Allow dirty builds"
        )
        argparser.add_argument(
            "--show-output",
            action="store_true",
            help="Show build output and don't write files",
        )
        argparser.add_argument(
            "--prefix",
            type=str,
            help="Help the script to determine correct prefix for GCC",
        )
        return argparser

    def initFiles(self) -> bool:
        # Check for submodules existence and update it if needed.
        if check_file(Path(".gitmodules")):
            try:
                popen_impl(["git", "submodule", "update", "--init"])
            except RuntimeError:
                return False
        if not check_file(self.toolchainDir):
            logging.error(f"Please make toolchain available at {self.toolchainDir}")
            return False
        return True

    def selectToolchain(self) -> bool:
        maybeExe = self.toolchainDir / "bin" / "clang"
        if check_file(maybeExe):
            self.toolchaincls = CompilerClang(maybeExe)
            logging.info("Detected clang toolchain")
        else:
            maybeExe = self.toolchainDir / "bin"
            if self.args.prefix:
                maybeExe /= f"{self.args.prefix}gcc"
                if not check_file(maybeExe):
                    logging.error("Toolchain with specified prefix does not exist.")
                    return False
            else:
                try:
                    archPrefix = CompilerGCC.ARCH_PREFIX[self.arch]
                except KeyError:
                    logging.error(f"Unknown arch: {self.arch}")
                    return False
                file = [
                    l
                    for l in maybeExe.iterdir()
                    if l.name.startswith(archPrefix) and l.name.endswith("gcc")
                ]
                if len(file) == 0:
                    logging.error("Could not auto detect prefix")
                    return False
                maybeExe = file[0]
                logging.info(f"Using {maybeExe}")

            self.toolchaincls = CompilerGCC(maybeExe)

        try:
            self.toolchaincls.test()
        except RuntimeError as e:
            logging.error(e)
            return False
        try:
            self.toolchaincls.version()
        except AssertionError as e:
            logging.error(e)
            return False
        self.toolchainDir = self.toolchainDir.absolute()
        return True

    # Meant to be overriden
    def verifyArgs(self) -> bool:
        return True

    def buildDefconfigList(self) -> "list[str]":
        return []

    def additionalMakeArgs(self) -> "list[str]":
        return []

    def zipName(self, name: str, time: str) -> str:
        return f"{name}Kernel_{time}.zip"

    def anykernelFiles(self) -> "list[str]":
        return []

    def preBuildInfo(self) -> "dict[str, str]":
        return {}

    def doBuild(self):
        print_dictinfo(
            {
                "TARGET_KERNEL": self.kernel_name,
                "USING_TOOLCHAIN": self.toolchaincls.version(),
                "START_TIME": str(datetime.now()),
            }
            | self.preBuildInfo()
        )

        # Add toolchain in PATH environment variable
        tcPath = self.toolchainDir / "bin"
        if tcPath not in os.environ["PATH"].split(os.pathsep):
            os.environ["PATH"] = f'{tcPath}:{os.environ["PATH"]}'

        if self.outDir.exists() and not self.args.allow_dirty:
            logging.debug(f"Removing {self.outDir}")
            shutil.rmtree(self.outDir)

        common_make = [
            "make",
            f"O={self.outDir}",
            f"-j{os.cpu_count()}",
            f"ARCH={self.arch}",
        ]
        maybeCrossComp = self.toolchaincls.cross_compile_arg(self.arch)
        if maybeCrossComp:
            common_make += maybeCrossComp
        common_make += self.additionalMakeArgs()
        make_defconfig: "list[str]" = []
        make_defconfig += common_make
        make_defconfig += self.buildDefconfigList()

        global popen_impl
        if self.args.show_output:
            def popen_impl(args):
                s = subprocess.Popen(args)
                s.wait()
                if s.returncode != 0:
                    raise RuntimeError(f'Process returned exit code {s.returncode}')
        t = datetime.now()
        logging.info("Make defconfig")
        popen_impl(make_defconfig)
        logging.info("Make kernel")
        popen_impl(common_make)
        logging.info("Done")
        t = datetime.now() - t

        kver = ""
        with open(self.outDir / "include" / "generated" / "utsrelease.h") as f:
            kver = match_and_get(r'"([^"]+)"', f.read())

        if self.anykernelDir:
            shutil.copyfile(
                self.outDir / "arch" / Path(self.arch) / "boot" / Path(self.kernelType),
                self.anykernelDir / Path(self.kernelType),
            )
            zipName = self.zipName(
                self.kernel_name, datetime.today().strftime("%Y-%m-%d")
            )
            os.chdir(self.anykernelDir)
            defFiles = [
                self.kernelType,
                "META-INF/com/google/android/update-binary",
                "META-INF/com/google/android/updater-script",
                "tools/ak3-core.sh",
                "tools/busybox",
                "tools/magiskboot",
                "anykernel.sh",
            ]
            defFiles += self.anykernelFiles()
            zip_files(zipName, defFiles)
            os.chdir("..")
            shutil.move(self.anykernelDir / Path(zipName), zipName)
            print_dictinfo(
                {
                    "OUT_ZIPNAME": zipName,
                    "KERNEL_VERSION": kver,
                    "ESCLAPED_TIME": str(t.total_seconds()) + " seconds",
                }
            )

    def build(self):
        self.args = self.initArgParser().parse_args()
        if not self.verifyArgs():
            logging.error("Failed to verify args")
            return
        if not self.initFiles():
            return
        if not self.selectToolchain():
            return
        self.doBuild()
