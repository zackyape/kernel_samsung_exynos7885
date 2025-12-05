import subprocess
from .loginit import logging

debug_popen_impl = False


def popen_impl(command: "list[str]"):
    s = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if debug_popen_impl:
        logging.debug(f"Executing command: \"{' '.join(command)}\"... has pid {s.pid}")
    out, err = s.communicate()

    def write_logs(out: str, err: str):
        stdout_log = str(s.pid) + "_stdout.log"
        stderr_log = str(s.pid) + "_stderr.log"
        with open(stdout_log, "w") as f:
            f.write(out)
        with open(stderr_log, "w") as f:
            f.write(err)
        logging.info(f"Output log files: {stdout_log}, {stderr_log}")

    if s.returncode != 0:
        if debug_popen_impl:
            logging.error(f"PID {s.pid}) result: Fail")
        write_logs(out, err)
        raise RuntimeError(f"Command failed: {command}. Exitcode: {s.returncode}")
    if debug_popen_impl:
        logging.info(f"PID {s.pid}) result: Success")
        write_logs(out, err)
