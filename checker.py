# from ipwhois import IPWhois
from dns import resolver
from geolite2 import geolite2
import re
import subprocess

wrk_cmd = '/usr/local/bin/wrk'


def get_bytes(size_str):
    x = re.search(r"^(\d+\.*\d*)(\w+)$", size_str)
    if x is not None:
        size = float(x.group(1))
        suffix = (x.group(2)).lower()
    else:
        return size_str

    if suffix == 'b':
        return size
    elif suffix == 'kb' or suffix == 'kib':
        return size * 1024
    elif suffix == 'mb' or suffix == 'mib':
        return size * 1024 ** 2
    elif suffix == 'gb' or suffix == 'gib':
        return size * 1024 ** 3
    elif suffix == 'tb' or suffix == 'tib':
        return size * 1024 ** 3
    elif suffix == 'pb' or suffix == 'pib':
        return size * 1024 ** 4

    return False


def get_number(number_str):
    x = re.search(r"^(\d+\.*\d*)(\w*)$", number_str)
    if x is not None:
        size = float(x.group(1))
        suffix = (x.group(2)).lower()
    else:
        return number_str

    if suffix == 'k':
        return size * 1000
    elif suffix == 'm':
        return size * 1000 ** 2
    elif suffix == 'g':
        return size * 1000 ** 3
    elif suffix == 't':
        return size * 1000 ** 4
    elif suffix == 'p':
        return size * 1000 ** 5
    else:
        return size

    return False


def get_ms(time_str):
    x = re.search(r"^(\d+\.*\d*)(\w*)$", time_str)
    if x is not None:
        size = float(x.group(1))
        suffix = (x.group(2)).lower()
    else:
        return time_str

    if suffix == 'us':
        return size / 1000
    elif suffix == 'ms':
        return size
    elif suffix == 's':
        return size * 1000
    elif suffix == 'm':
        return size * 1000 * 60
    elif suffix == 'h':
        return size * 1000 * 60 * 60
    else:
        return size

    return False


def parse_wrk_output(wrk_output):
    retval = {}
    for line in wrk_output.splitlines():
        x = re.search(r"^\s+Latency\s+(\d+\.\d+\w*)\s+(\d+\.\d+\w*)\s+(\d+\.\d+\w*).*$", line)
        if x is not None:
            retval['lat_avg'] = get_ms(x.group(1))
            retval['lat_stdev'] = get_ms(x.group(2))
            retval['lat_max'] = get_ms(x.group(3))
        x = re.search(r"^\s+Req/Sec\s+(\d+\.\d+\w*)\s+(\d+\.\d+\w*)\s+(\d+\.\d+\w*).*$", line)
        if x is not None:
            retval['req_avg'] = get_number(x.group(1))
            retval['req_stdev'] = get_number(x.group(2))
            retval['req_max'] = get_number(x.group(3))
        x = re.search(r"^\s+(\d+)\ requests in (\d+\.\d+\w*)\,\ (\d+\.\d+\w*)\ read.*$", line)
        if x is not None:
            retval['tot_requests'] = get_number(x.group(1))
            retval['tot_duration'] = get_ms(x.group(2))
            retval['read'] = get_bytes(x.group(3))
        x = re.search(r"^Requests\/sec\:\s+(\d+\.*\d*).*$", line)
        if x is not None:
            retval['req_sec_tot'] = get_number(x.group(1))
        x = re.search(r"^Transfer\/sec\:\s+(\d+\.*\d*\w+).*$", line)
        if x is not None:
            retval['read_tot'] = get_bytes(x.group(1))
        x = re.search(
            r"^\s+Socket errors:\ connect (\d+\w*)\,\ read (\d+\w*)\,\ write\ (\d+\w*)\,\ timeout\ (\d+\w*).*$", line)
        if x is not None:
            retval['err_connect'] = get_number(x.group(1))
            retval['err_read'] = get_number(x.group(2))
            retval['err_write'] = get_number(x.group(3))
            retval['err_timeout'] = get_number(x.group(4))
        x = re.search(r"^Non-2xx or 3xx responses\:\s+(\d+).*$", line)
        if x is not None:
            retval['non2xx'] = get_number(x.group(1))
    if 'err_connect' not in retval:
        retval['err_connect'] = 0
    if 'err_read' not in retval:
        retval['err_read'] = 0
    if 'err_write' not in retval:
        retval['err_write'] = 0
    if 'err_timeout' not in retval:
        retval['err_timeout'] = 0
    if 'non2xx' not in retval:
        retval['non2xx'] = 0
    retval['err_rate'] = retval['non2xx'] * 100 / retval['tot_requests'] if retval['tot_requests'] != 0 else 100
    return retval


def execute_wrk(threads, concurrency, duration, timeout, domain, ip):
    cmd = [f'{wrk_cmd}', '--timeout', f'{timeout}', '-d', f'{duration}s', '-c', f'{concurrency}', '-t', f'{threads}',
           '-H', f"'Host:\ {domain}'", f'https://{ip}/']
    process = subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.PIPE,
        universal_newlines=True)
    output = process.stdout
    return output


def main():
    dns = resolver.Resolver()
    dns.nameservers = ['8.8.8.8']

    reader = geolite2.reader()

    print("{:<30} {:<15} {:<7} {:<10} {:<10} {:<10}".format("Domain", "IP", "Country", "Latency", "RPS", "Error Rate"))
    with open('domains.txt', 'r') as f:
        domains = [d.strip() for d in f.readlines()]
        for domain in domains:  # for every domain in file
            ips = dns.resolve(domain)  # get IPs from resolver
            for ip in ips:  # for each IP
                # country = IPWhois(ip).lookup_whois()["asn_country_code"]  # get IP country from WHOIS
                match = reader.get(f'{ip}')
                if match:
                    # print(match)
                    if 'country' in match:
                        country = match['country']['iso_code']
                    else:
                        country = match['continent']['code']
                else:
                    country = "Unknown"
                wrk_dict = parse_wrk_output(execute_wrk(20, 50, 5, 10, domain, ip))  # get stats from WRK
                print(
                    "{:<30} {:<15} {:<7} {:<10} {:<10} {:<10}".format(f"{domain}", f"{ip}", f'{country}',
                                                                      f"{wrk_dict.get('lat_avg')}",
                                                                      f"{wrk_dict.get('req_sec_tot')}",
                                                                      # f"{wrk_dict.get('tot_requests')}",
                                                                      # f"{wrk_dict.get('non2xx')}",
                                                                      f"{wrk_dict.get('err_rate')}%"))


if __name__ == '__main__':
    main()
