# Your team pod: t11

This environment holds an NVIDIA RTX A6000 (48 GB), 28 CPU cores, 56 GB of RAM, Ubuntu 22.04, and one Kubernetes cluster (k3s) with the card already in its ledger. The login is `ubuntu` for everyone. It runs without a break until 1 October, so nothing here needs stopping, and everything you leave on it is the team's.

You are encouraged to experiment on this GPU.

## Ways in

**This IDE, in the browser.** `https://t11-ide.aidc.nadir.sh` and the team password. The terminal is `` Ctrl+` `` (Terminal > New Terminal) and opens in `~/aidc`. Four browsers can be open at once; each gets its own terminals, and you all see the same files. *Be careful not to edit the same file at the same time.*

**SSH from your own machine, no browser.** The pod has no public address; SSH rides the same tunnel as this page. Once per person, from a terminal here, add your laptop's public key:

```bash
echo 'ssh-ed25519 AAAA...your key...' >> ~/.ssh/authorized_keys
```

Then on your laptop, with `cloudflared` installed (the lab's install block), put this in `~/.ssh/config`:

```
Host t11
  HostName t11-ssh.aidc.nadir.sh
  User ubuntu
  ProxyCommand cloudflared access ssh --hostname %h
```

and `ssh t11` is your shell on the pod. VS Code Remote-SSH, Cursor and `scp`/`rsync` all work against that host. `tmux` is installed for anything that should outlive your connection (a port-forward, a load run).

**Nothing else is exposed.** The cluster's API is not on the tunnel, so `kubectl` runs on the pod, in this IDE or over SSH, never from your laptop.

## Where things are

- The labs live on the learning platform, not here. Each day you make a folder in your directory, write the manifests the lab shows you, and bring its given files across (paste into a new file, or right-click the folder in the explorer, **Upload...**; `scp` over SSH works too).
- `~/aidc/<you>/` your directory: your lab folders and your `kubeconfig`.
- `~/aidc/README.md` this file.
- `/var/lib/hf-cache/` the model cache the engine reads (Qwen2.5-1.5B-Instruct-AWQ is already there).
- `/etc/aidc-pod` the pod's identity, if a script needs it.

## The cluster, in four lines

- `kubectl` works as `ubuntu`. Each of you exports your own copy of the kubeconfig in **every** terminal: `export KUBECONFIG=~/aidc/<you>/kubeconfig` (D1 Step 0 makes it, with your namespace set as its default).
- One namespace each, named after you: your pods never collide with a teammate's. `kubectl config view --minify | grep namespace:` says where you are.
- The `team` namespace is the team's: the engine on the card (Tuesday) and the public endpoint (Thursday) live there. Switch with `kubectl config set-context --current --namespace=team`, and back with `--namespace=<you>`.
- Two ports are wired to the outside world by the pod's tunnel: NodePort **30800** is `https://t11.aidc.nadir.sh` (the team endpoint, Thursday) and NodePort **30300** is `https://t11-graf.aidc.nadir.sh` (Grafana, week 5). Everything else stays inside.

## The card

`nvidia-smi` shows it. The scheduler hands it to one pod at a time, so a pod that asks for `nvidia.com/gpu: 1` while another holds it sits `Pending` with `Insufficient nvidia.com/gpu`. From Tuesday the team engine holds it for the rest of the course; never leave a test pod sleeping on it.

## House rules

- Work in your namespace; touch `team` only when the team agreed.
- No `sudo` into k3s, docker or the tunnel unless a lab says so, and no reboots. If the pod is truly broken, tell the instructor: it can be rebuilt from its image in about ten minutes, and everything on it goes with it.
- Commit to the team repository. The pod is where things run, not where they are kept.
