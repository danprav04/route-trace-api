import tracer.routetrace.regex_patterns
import re


def get_int_from_subint_if_subint(sub_interface_suspect):
    if sub_interface_suspect.lower().startswith('vl'):
        return None

    if '.' in sub_interface_suspect:
        interface = sub_interface_suspect.split('.')[0]
        if re.match(pattern=regex_patterns.interface_pattern, string=interface.lower()):
            return interface
    return None
