set -eux
cd "$(dirname "$0")/.."

west update

if [ "$#" -eq 1 ]; then
	git -C zephyr checkout "$1"
fi

west bflb-test run -- \
-s arch.riscv.fpu_sharing \
-s arch.riscv.pm_s2ram.clic \
-s drivers.console.uart \
-s drivers.flash.common.default \
-s drivers.flash.common.test_storage_partition \
-s drivers.gpio.get_direction \
-s pm.device_runtime \
-s sample.basic.helloworld \
-s sample.kernel.philosopher \
-s kernel.cache.api \

west bflb-test push
