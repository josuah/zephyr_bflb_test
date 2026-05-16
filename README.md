Zephyr test Rig for BouffaloLab
===============================

This is a set of scripts for testing various boards and publish the results periodically.

It uses an external USB UART adapter:

- Power supply via GND and 3.3V pin
- TX and RX to transfer the data (firmware via bootloader and test results)
- DTR pin for BOOT toggling
- RTS pin for RESET toggling

## Preparing

Clone with west:

```
mkdir ~/zephyrproject
cd ~/zephyrproject
west init -m git@github.com:josuah/zephyr_test_rig
west update
```

You need to patch twister for DTR/RTS handling
(note that `west patch clean` might silently discard your uncommitted data):

```
west patch apply
```

## Running tests

Example session:

```
# Initialize the rig
west bflb-test init rig0

# Add two boards
west bflb-test set /dev/ttyACM0 ai_m61_32s_kit
west bflb-test set /dev/ttyACM1 ai_wb2_12f_kit

# Run various tests, results will be stored in the repo
west bflb-test run -- -T samples/hello_world/ --log-level DEBUG

# Publish the tests results
west bflb-test push
```

See `west bflb-test` help text for full usage.
