# merlin kernel — Redmi Note 9（merlin / merlinx，MT6768）

给这台机器补**容器能力（Droidspaces / Docker）**的内核与 boot 镜像仓库。
配置一律以设备自己的 `/proc/config.gz` 为底，只追加容器缺项，硬件驱动不动。

> 历史：本仓库早期针对 MIUI 12.5 / AOSP 11 Pixel 移植版（4.14.246-pizza）。
> 那台机器现在跑的是 Infinity-X（Android 17，4.19.325），配置和版本串全部作废，
> 已按新 ROM 重新采集。旧内容仍可从 git 历史取回。

## 当前版本

| 项目 | 值 |
|---|---|
| 机型 | Redmi Note 9，`ro.product.device=merlin`，`ro.product.name=merlinx` |
| 系统 | Infinity-X，Android **17**（LineageOS 24.0 基座） |
| 版本 | `ro.build.id=CP2A.260605.016`，安全补丁 `2026-10-01` |
| 内核 | `4.19.325-cip136-st20-Skyron` |
| 分区 | 非 A/B，`boot=/dev/block/mmcblk0p33`（64 MiB），无 `init_boot` |

### 下载

- **v1.0** → [Releases · v1.0-4.19.325-cip136](https://github.com/GACN/merlin-kernel-container/releases/tag/v1.0-4.19.325-cip136)
  - `boot_merlin_4.19.325-cip136-container-v1.0.img`
  - md5 `f584fe6ba05420c9b90b574f5d4d0c1b`
  - sha256 `2dbc52df06ba61b41fc630484b82102ff6192e26f3ffc0afa16be551a4b94621`

## 增量内容

容器硬缺项（Droidspaces 自检的致命项 `[✗] IPC namespace` 就是它）：

```
SYSVIPC  SYSVIPC_SYSCTL  IPC_NS  USER_NS  POSIX_MQUEUE
CGROUP_PIDS  CFS_BANDWIDTH  DEVTMPFS
```

Docker 网络：

```
MACVLAN  VXLAN  IP6_NF_NAT  IP6_NF_TARGET_MASQUERADE  NETFILTER_XT_MATCH_ADDRTYPE
```

链接修复：LCM 与 `disp_recovery.c` 无条件引用 Novatek 触摸符号，而真机触摸是
focaltech（`fts_ts`），该驱动未启用 → `drivers/misc/mtk_lcm_stub.c` 提供
`nvt_gesture_flag` / `nvt_update_firmware` 最小桩，不注册驱动、不 probe 硬件。

## 为什么不能照抄别人的配置

这台 ROM 一个可加载模块都没有：`/vendor/lib/modules` 里只有 `kheaders.ko`，
WiFi / 蓝牙 / 显示 / 触摸 / 指纹全部 **builtin** 编进内核。漏一项就是硬件直接不工作。
所以 `config/base.config` 直接取自设备 `/proc/config.gz`，只追加容器项。

## 刷入 / 回滚

```sh
# 刷
fastboot flash boot boot_merlin_4.19.325-cip136-container-v1.0.img

# 回滚（原 Magisk boot）
md5sum boot_current_magisk.img      # 必须 = 76aac978b4cd391604a3e33992968136
fastboot flash boot boot_current_magisk.img
```

## 构建

`GACN/merlinx-ksu-boot`（私有）里的 `build-containers.yml`：clang-12 全量编译 4.19 MTK 树，
`ci/repack.py` 按原 boot header（v2 / page 2048）重打包，ramdisk 沿用设备上已 Magisk 打过补丁的那份，
刷完 Root 与模块不丢。

## 注意

- 内核**没有** SUSFS：春秋检测里的 LineageOS / Mount loophole 一类不会因为刷这个内核消失
- 不要再拿 Magisk App 二次 patch 这个镜像（ramdisk 已 patch 过）
