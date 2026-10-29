# merlin-container-kernel

给 **Redmi 10X 4G / Redmi 10X 4G (merlin, MediaTek MT6768)** 从官方开源内核源码编译一个
**带容器支持（droidspaces / Docker 底座）** 的内核，可选内置 **KernelSU**。

内核版本：4.14.186（非 GKI）· 源码：小米 R 版 OSS 内核（mitsu00/merlin-r-oss）

本仓库**不含内核源码，也不含编译产物**（Image.gz-dtb / 刷机包）。仓库里只有把源码编成
可用内核所必需的那一层"脚手架"：CI 流程、原厂配置、增量配置、以及让老代码在现代 clang
下编得过的补丁脚本。

---

## 为什么需要这个仓库

原厂内核没有容器要的隔离/限额能力；自己从零写配置会漏掉一堆 MTK 私有开关，
编出来的内核能跑但屏、触摸、基带全废。所以做法是：

    config/base.config   原厂 ROM 的完整内核配置（4109 项，原样保留）
  + config/extra.config  只加容器相关的增量开关（约 20 行）
  + 四处必需补丁         （见下）
  → olddefconfig 自动补全依赖 → make Image.gz-dtb

结果是一个版本串与原厂完全一致、但多了容器能力的内核。

## 仓库内容

| 路径 | 作用 |
|---|---|
| `.github/workflows/build.yml` | GitHub Actions 流程：拉源码 → 打补丁 → 配置 → 编译 → 校验 → 打包 |
| `config/base.config` | 官方 ROM 内核配置全文（厂商驱动、面板、触摸、存储、文件系统全在） |
| `config/extra.config` | 增量：命名空间 / cgroup / overlayfs / 容器网络 / SYSVIPC / LOCALVERSION |
| `tools/patch_makefile.py` | clang + GNU binutils 组合所需的 Makefile 调整 |
| `tools/add_ksu_hooks.py` | KernelSU v0.9.5 的 4 处手工 hook（非 GKI 4.14 必需） |

容器开关（实际生效比原厂多 16 项）：
`SYSVIPC` `SYSVIPC_SYSCTL` `POSIX_MQUEUE` `IPC_NS` `USER_NS` `UTS_NS` `PID_NS` `NET_NS`
`CGROUP_DEVICE` `CGROUP_PIDS` `CGROUP_NET_PRIO` `CGROUP_NET_CLASSID` `BLK_CGROUP`
`OVERLAY_FS`（+INDEX/REDIRECT_DIR）`MACVLAN` `IPVLAN` `VXLAN` `NET_IPIP`
`BRIDGE_NETFILTER` `XT_MATCH_ADDRTYPE` `XT_MATCH_MULTIPORT` ×

## 四处必需补丁（少一个就编不过）

1. **厂商固件 blob 占位** — MTK OSS 树里 focaltech 触摸驱动的
   `focaltech_config.h` 引用 `include/firmware/fw_sample.i`，这个固件字节数组没有随源码发布，
   编译直接 `file not found`。补零填充占位（运行时驱动走 `request_firmware()` 从 /vendor 取真固件）。
2. **全树 `-Werror` → `-Wno-error`** — `kernel/Makefile` 里有一批
   `-Werror=strict-prototypes` / `-Werror=implicit-int` 形态的开关，`KCFLAGS=-Wno-error` 压不住，
   必须改写 Makefile 本身；否则 2019 年的代码在 clang 24 下几百个警告全变错误。
3. **补 `stpcpy()`** — clang ≥19 会把部分 `strcpy` 模式降成 `stpcpy()` 调用（即使 `-fno-builtin`），
   4.14 没有这个函数，链接期 `undefined reference to stpcpy`。往 `lib/string.c` 追加实现 + `EXPORT_SYMBOL`，
   函数挂 `__attribute__((optnone))` 防止被改写成自调用。
4. **掐掉版本串里的 `+`** — kbuild 的 `scripts/setlocalversion` 在 git 树 dirty 时自动追加 `+`，
   而打补丁必然弄脏树，于是 `...-gxxxx+` 与厂商模块要求的 `...-gxxxx` 不一致。
   **vermagic 对不上，厂商 `.ko` 全部拒载**——表现为 Wi-Fi、摄像头、音频等模块化硬件全挂。

## 版本串（vermagic）是这套流程的关键

Android 4.14 内核按 vermagic 全串严格匹配厂商模块。真值只能从目标 ROM 里取：

```bash
# 1) 从 ROM 的 boot.img 里取原厂内核版本串
strings <解压出的 kernel> | grep -m1 'Linux version'
# 2) 或从官方 ROM 的 vendor.img 里取模块 .modinfo（注意：必须是对应这台机器这个 ROM 的镜像）
strings vendor.img | grep -oE '4\.14\.[0-9]+[^ ]* SMP preempt mod_unload[^"]*' | sort | uniq -c
```

把拿到的 localversion 后缀写进 `config/extra.config` 的 `CONFIG_LOCALVERSION`，
CI 里有一道**硬门禁**：编完把镜像解开比对 vermagic，不一致直接 fail。

> 本仓库默认值 `-g46ead2c21af1` 来自 MIUI 12.5.7.0（`miui_MERLIN_V12.5.7.0.RJOCNXM`）的 boot.img。
> 换 ROM 就必须改这个值，否则模块全拒载。

## 两个构建变体

| 变体 | 内容 |
|---|---|
| `plain` | 容器支持内核，无 root |
| `ksu` | 同上 + KernelSU **v0.9.5**（KernelSU 1.0 起不再支持非 GKI 内核，4.14 只能用 0.9.5 + 手工 hook） |

产物：`Image.gz-dtb`（内核 + 附加 dtb）与 AnyKernel3 刷机包。
AnyKernel3 只替换内核，ramdisk 与 dtb 沿用设备现有 boot，因此 dtb 一定来自目标机可点亮的 boot。

## 已知状态与风险

- **编译通过**（两个变体均 success），配置与版本串经脚本核验。
- **未在真机验证** —— 本仓库的作者没有把产物刷上机测试过。自行承担风险，刷前先备份 boot。
- `config/base.config` 中有 6 项小米私有开关（`KTRACE` `MIGT` `MIHW` `MIUI_ZRAM_MEMORY_TRACKING` `RTMM` `SERIAL_NUM`）
  在 OSS 源码树里不存在，`olddefconfig` 会自动丢弃，MIUI 专有的部分 sysfs 节点会缺失。
- `CONFIG_MODVERSIONS=y`：模块符号 CRC 仍需与厂商模块对齐，源码同源一般没问题，
  真报 `disagrees about version of symbol` 就是这里。

## 使用

```bash
# fork 本仓库 → Actions → "Build merlin kernel (container + optional KernelSU)" → Run workflow
```

需要自备 GitHub Actions（免费额度足够，单次约 12–20 分钟）。

## 许可与来源

- 内核源码版权归小米 / 上游 Linux 内核作者所有（GPL-2.0）。
- `config/base.config` 取自官方 ROM 内核对外的配置，`config/extra.config` 与 `tools/` 下的脚本为本仓库原创。
- 仅供个人设备的内核编译实验，不提供任何形式的担保。
