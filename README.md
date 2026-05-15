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

You need to patch twister for DTR/RTS handling:

```
west patch apply
```

Then you can use the `west bflb` commands.

## Running tests

[[[ These are not implemented yet ]]]

- `west bflb-rig init <name>` initate your test rig using `west config`.
  This name will be used by other commands.

- `west bflb-rig add <board> <serial>` add a board name
  and serial (i.e. `/dev/ttyACM0`) to your own hardware map file in the repo.

- `west bflb-rig run <extra-twister-args>...` will run twister with default
  arguments and store the results under a standard name.

- `west bflb-rig html` will generate an HTML report of all the tests
  currently stored, for use in combination with static website generators.

- `west bflb-rig push` will git commit/push the results, so that they can be
  visualized online.
