from pathlib import Path
from .base import CompilerBase

class CompilerGCC(CompilerBase):
    def __init__(self, exePath: Path):
        self.exe_path = exePath
        self.versionRe = r"(.*?gcc \(.*\) \d+(\.\d+)*)"

    def _cross_compile_arg(self, arch: str):
        return self.exe_path.name[:-3]

    # The general CROSS_COMPILE target
    TARGET_TRIPLES = {
        "arm": "arm-linux-gnueabi",
        "arm64": "aarch64-linux-gnu",
        "riscv": "riscv64-linux-gnu",
        "x86": "x86_64-linux-gnu",
    }

    # Map ARCH= value to gcc prefix
    ARCH_PREFIX = {
        "arm": "arm",
        "arm64": "aarch64",
        "riscv": "riscv64",
        "x86": "x86_64",
    }
