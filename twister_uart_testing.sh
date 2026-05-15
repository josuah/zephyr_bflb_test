#!/bin/sh
set -eu

if [ $# -le 1 ]; then
    echo >&2 "example: sh $0 /dev/ttyACM0 -p ai_m61_32s_kit -s sample.kernel.philosopher"
    exit 1
fi

serial=$1
shift 1

# Main command flags
cmd="west twister --device-testing"

# Very verbose: expect not to work on first try
cmd="$cmd --log-level DEBUG"

# Wait that the flashing is done before attaching the console
cmd="$cmd --flash-before"

# Pass the serial console as argument to "west flash"
cmd="$cmd --west-flash=--dev-id=$serial"

# bflb-mcu-tool-uart will leave the board with RTS set to logic low (i.e. 3.3V).
# When connected to RESET, this holds it until we set it to logic high (i.e. 0.0V)
# with i.e. picocom or another command
#cmd="$cmd --device-serial-pty=picocom,--baud=115200,--lower-rts,$serial"
cmd="$cmd --device-serial=$serial"

# Print the command and run it
echo $cmd "$@"
exec $cmd "$@"
