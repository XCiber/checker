# Checker

Checker is a python script which collect some benchmarks for domains listed in file 

## Installation

clone this repo

```bash
git clone https://github.com/XCiber/checker.git
cd checker
```

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install dependencies.

```bash
pip install -r requirements.txt
```

This script also require [wrk](https://github.com/wg/wrk) for benchmarking. So you have to install it

Debian/Ubuntu
```bash
apt-get install wrk
```

OS X
```bash
brew install wrk
```

and change path to wrk executable in the top of checker.py file

```python
wrk_cmd = '/usr/local/bin/wrk'
```

## Usage

fill the domains.txt file with domain-names you want to check

domains.txt
```text
exness.com
```

start script
```bash
./checker.py
```

## Example output
```bash
Domain                         IP              Country Latency    RPS        Error Rate
exness.com                     45.60.133.64    US      68.7       3.17       0.0%      
exness.com                     45.60.78.64     US      88.61      3.36       0.0%      
```