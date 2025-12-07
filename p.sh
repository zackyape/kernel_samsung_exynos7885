#!/bin/bash

# Replace all lines starting with "#ifdef CONFIG_KPROBES"
# into "#if defined(CONFIG_KPROBES) && 0"

find . -type f \( -name "*.c" -o -name "*.h" \) -print0 | while IFS= read -r -d '' file
do
    sed -i.bak 's/^#ifdef[[:space:]]\+CONFIG_KPROBES/#if defined(CONFIG_KPROBES) \&\& 0/' "$file"
done

echo "Done! Semua #ifdef CONFIG_KPROBES sudah diganti."
