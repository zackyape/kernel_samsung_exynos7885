from pathlib import Path
from .base import CompilerBase
from .gcc import CompilerGCC

class CompilerClang(CompilerBase):
    def __init__(self, exePath: Path):
        self.exe_path = exePath
        self.versionRe = r"(.*?clang version \d+(\.\d+)*).*"

    def _cross_compile_arg(self, arch: str):
        try:
            return CompilerGCC.TARGET_TRIPLES[arch]
        except KeyError:
            return ''

    ADDITIONALARGS_LLVM_FULL = ["LLVM=1", "LLVM_IAS=1"]
    ADDITIONALARGS_BASE = ["CC=clang"]
