# merlin kernel — Redmi Note 9 (merlin / merlinx, MT6768)

给这台机器的 AOSP 11 Pixel 移植版编内核：**容器/Docker 能力** + 可选的**内核内置免休眠守护**。

| 项目 | 值 |
|---|---|
| 设备 | Redmi Note 9，`ro.product.device=merlin`，`ro.product.name=merlinx` |
| 系统 | AOSP 11，`RQ3A.210905.001`，SDK 30，`aosp_merlinx-user` |
| 当前内核 | `4.14.246-pizza`（`CONFIG_LOCALVERSION="-pizza"`） |
| 源码 | [Redmi-MT6768/android_kernel_xiaomi_mt6768](https://github.com/Redmi-MT6768/android_kernel_xiaomi_mt6768) 分支 `eleven`（pizza+ kernel，4.14.248） |
| 编译器 | AOSP `clang-r383902b`（clang 11.0.2，与原 ROM 同一个编译器） |

> 历史：本仓库早期版本针对的是 MIUI 12.5.7 的 `4.14.186-g46ead2c21af1`。
> 那台机器后来刷成了 Pixel A11 移植版，内核变成 `4.14.246-pizza`，配置和版本串全部作废，
> 已按新 ROM 重新采集。旧内容仍可从 git 历史里取回。

## 为什么不能照抄旧配置

这台 ROM **一个可加载模块都没有**——`/vendor/lib/modules` 不存在，`find /vendor /odm /system -name '*.ko'` 返回 0。
WiFi、蓝牙、显示、触摸、指纹全部 **builtin** 编在内核里。

后果有两条：

1. 没有 `.ko` 可拒载，所以 vermagic 不需要和厂商模块逐字对齐（旧仓库那道硬门禁在这里没有意义）。
2. 但所有厂商驱动都在内核镜像里，`base.config` 必须就是这台 ROM 自己的配置，漏一项就是硬件直接不工作。

所以 `config/base.config` 直接取自设备 `/proc/config.gz`（5168 行，原样未改），
`config/extra.config` 只追加容器能力。CI 里有一道门禁：编完如果 `MTK_COMBO_WIFI`、
`MTK_COMBO_BT`、`MTK_FINGERPRINT_SUPPORT`、`MTK_LCM`、`MTK_ION`、`MTK_WATCHDOG` 任何一项丢失，构建直接失败。

## 增量内容（extra.config）

容器硬缺项（Droidspaces 自检里 `[✗] IPC namespace` 就是它）：

```
SYSVIPC  SYSVIPC_SYSCTL  IPC_NS  USER_NS
CGROUP_PIDS  CGROUP_DEVICE  CFS_BANDWIDTH
DEVTMPFS
```

Docker 网络：

```
NF_TABLES(+INET/IPV4/IPV6/NETDEV)  XT_MATCH_ADDRTYPE  XT_MATCH_MULTIPORT
IP6_NF_NAT  IP6_NF_TARGET_MASQUERADE  MACVLAN
```

`DEVTMPFS_MOUNT` 故意不开——Android 自己会用 tmpfs 盖住 `/dev`。

## 两个变体

| 变体 | 内容 |
|---|---|
| `plain` | 原 ROM 配置 + 容器能力 |
| `guard` | 同上 + 内核内置免休眠守护（`scripts/guard_patch.py`） |

`guard` 的作用是替掉 `merlinx-no-suspend-guard` 这个 Magisk 模块：在
`kernel/power/suspend.c` 的 `late_initcall` 里注册一个 wakeup source 并常持，
让 SoC 停在 idle 而不进入那条会死锁的 MTK 深度 suspend 路径。

根因取证（`/sys/fs/pstore` + DropBox + dmesg）：

```
ION/composer screen-off → sensorHub suspend → Freezing of tasks aborted
→ connsys clock check fail → 内核日志停止 → MTK watchdog 复位
```

息屏到断气约 9.5 秒。持锁后实测息屏 18 秒 ADB 仍在线、按电源键能回到 `Awake`。

启动时想关掉它：内核命令行加 `merlinx_no_suspend=0`。

## 必需补丁（少一个就编不过）

1. `tools/patch_makefile.py` — `CLANG_FLAGS --prefix` 必须带 triple，否则 clang 调用宿主机 `as`；
   并把 `-Werror` 系列（含 `subdir-ccflags-y` 形态）压成 `-Wno-error`。
2. **厂商固件 blob 占位** — MTK OSS 树的 focaltech 触摸驱动引用 `include/firmware/*.i`，
   这些字节数组没随源码发布。按**引用它的 .c 所在目录**建零填充占位（不是 `kernel/include/`）。
3. **掐掉版本串里的 `+`** — 打补丁会让 git 树 dirty，`scripts/setlocalversion` 会自动加 `+`。

用 clang 11 时不需要补 `stpcpy`（那是 clang ≥19 的问题）。

## 使用

Actions → `Build merlinx kernel` → Run workflow。

产物：

- `Image-<variant>.gz` — 纯 gzip 内核流，用来塞回 boot.img 的 kernel 段
- `Image-<variant>.gz-dtb` — 内核 + 源码树 dtb
- `built-config-<variant>.txt` — 实际生效的配置，用于逐项核对

## 刷入方式

**不要**用源码树的 dtb。当前 boot.img 是 header v2 / page 2048：

```
kernel 段 : gzip 14,626,362 字节
ramdisk   : gzip   744,834 字节
dtb 段    :       109,264 字节（独立段，不在 kernel 里）
```

重打包时 kernel 段换成 `Image-<variant>.gz`，ramdisk 和 dtb 段**逐字节沿用原 boot**，
并重算 header 的 sha1。原 boot 备份：

```
/storage/emulated/0/Music/每日归档/2026-10/梅岭手机-内核基线备份-20261030/boot.img
sha256 2790b5e843d8338d20fd6b65f9a5b41767bae1808067774800dc1170c909e1bc
```

## 状态

- [x] 源码/编译器/配置已锁定，补丁脚本在真实源码上验证可打
- [ ] CI 编译通过
- [ ] 真机启动验证（WiFi / 蓝牙 / 指纹 / 息屏唤醒 / Droidspaces / Docker）

## 许可

内核源码版权归 Xiaomi 与上游 Linux 作者（GPL-2.0）。本仓库只有 CI 脚手架与配置。
