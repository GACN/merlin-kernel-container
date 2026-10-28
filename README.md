# merlin container kernel

Rebuild of the Shockwave 4.14 kernel for Redmi Note 9 / 10X 4G (merlin, MT6768) with the config options needed by droidspaces + docker.

Base config is the exact IKCONFIG extracted from `[A11+]ShockwaveKernel-PxKN-merlin-202601031040.zip`; `config/extra.config` adds IPC/SYSVIPC, cgroup device/pids, addrfilter, bridge-netfilter, macvlan/ipvlan/vxlan.
