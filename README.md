Zephyr test Rig for BouffaloLab
===============================

This is a set of scripts for testing various boards and publish the results periodically.

It uses one USB UART adapter per board:

- Power supply via GND and 3.3V pin
- TX and RX for bootloader or runtime
- DTR/RTS pin for BOOT and RESET toggling

## Preparing

Clone with west:

```bash
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

## Plugging

Example:

![](docs/test_rig_diagram.png)

![](docs/test_rig_example.png)

Connecting an USB UART adapter to a board:

```
-------------.                         .--------------
            === GND ------------- GND ===
            === 3V3 ------------- 3V3 ===
   USB      === TX --------------- RX ===     DUT
   UART     === RX --------------- TX ===
            === RTS ---------- RESETN ===
            === DTR ------------ BOOT ===
-------------'                         '--------------
```

**Using the WeACT USB-UART, I have to unplug the DTR line, then power the board,
then plug DTR, or it would not toggle.**

Using `/dev/serial/by-id/...` instead of `/dev/ttyACM0` gives stable names.

## Testing

West flash test command (resetting the board to bootloader mode itself):

```bash
west flash --dev-id=/dev/ttyACM0
```

West twister test comand:

```bash
west twister --device-testing --log-level DEBUG --flash-before \
   --platform ai_m61_32s_kit --scenario samples.basic.helloworld \
   --west-flash=--dev-id=/dev/ttyACM0 --device-serial=/dev/ttyACM0
```

## Running

```bash
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

## `ai_wb2_12f_kit`

When it does not have the `BOOT` pin exposed due to missing parts (DNI).

An external USB-UART adapter is used instead, and the missing
BOOT signal is broken out from the module to a pin header.

![](docs/ai_wb2_12f_kit_rework.jpg)
