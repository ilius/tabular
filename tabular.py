#!/usr/bin/env python3
"Parse ASCII tabular output from commands such as docker ps or netstat -tanp"
import argparse
import sys
import re
import json
from collections import OrderedDict


def parse(
	filename: str,
	skip: int = 0,
	data_from_tests: "Optional[Iterable[str]]" = None,
) -> "List[Dict]":
    if data_from_tests:
        lines = data_from_tests
    else:
        if filename == "-":
            fp = sys.stdin
        else:
            fp = open(filename, encoding="utf-8")
        lines = fp.readlines()
        fp.close()
    if skip:
        lines = lines[skip:]
    else:
        # consider dwimming skipping lines
        # the heuristic is: assume that a line with only single spaces is text
        # and a line with multiple spaces is a column
        # we only dwim one line skip; we could keep looking for single-space
        # lines until we find a proper header line, but since the only
        # example known so far is netstat, we'll just check the first
        if len(re.findall(r"\s\s", lines[0])) == 0 and \
           len(re.findall(r"\s\s", lines[1])) > 0:
            lines = lines[1:]
    return parse_lines(lines)


def parse_lines(lines: "Iterable[str]") -> "List[Dict]":
    # handle ascii art tables. We remove all lines that are
    # composed of nothing but + and -
    lines = [x for x in lines if x.replace("-", "").replace("+", "").strip()]

    # if the first line now contains more than one | then we
    # assume that the divider is | not " "
    divider = " "
    lb_re = r" [^ ]"
    rb_re = r"[^ ] "
    if lines[0].count("|") > 1:
        divider = "|"
        lb_re = r"\|[^|]"
        rb_re = r"[^|]\|"

    # ss tries to be clever and have rows that look like
    #           Address:Port
    #    blah.blah.blah 12345
    # which is basically a right col and a left col with a weird header divider
    # so replace "x:x" with "x x" in headers, where x is a valid character
    lines[0] = re.sub(r"(\S):(\S)", r"\1 \2", lines[0])

    left_boundaries = [0] + [
        x.span()[0] + 1 for x in re.finditer(lb_re, lines[0])
    ]
    right_boundaries = [
        x.span()[0] + 1 for x in re.finditer(rb_re, lines[0])
    ]
    # Columns might be left-justified, or right-justified
    # Column headers may contain a space, or not
    # So, check each row, and then look at all the left boundaries: if there is
    #   a space before the left boundary and a character after it, then this
    #   is probably the actual beginning of a left-justified column
    # And look at all the right boundaries: if there is a character before the
    #   right boundary and a space after it, then this is probably the actual
    #   end of a right-justified column
    lb_checked = {
    	b: [] for b in left_boundaries
    }
    rb_checked = {
        b: [] for b in right_boundaries
    }
    for line in lines[1:]:  # skip the headers
        if not line:
            continue
        for lb in lb_checked:
            if lb == 0:
                lb_checked[lb].append(line[lb] != divider)
            elif lb > len(line):
                lb_checked[lb].append(False)
            else:
                lb_checked[lb].append(
                    line[lb] != divider and line[lb - 1] == divider
                )
        for rb in rb_checked:
            if rb > len(line):
                rb_checked[rb].append(False)
            else:
                rb_checked[rb].append(
                    line[rb - 1] != divider and line[rb] == divider
                )
    valid_lb = [x[0] for x in lb_checked.items() if all(x[1])]
    valid_rb = [x[0] for x in rb_checked.items() if all(x[1])]
    position = 0
    columns = []
    while valid_lb or valid_rb:
        if valid_lb and valid_rb:
            if valid_lb[0] < valid_rb[0]:
                nxt = (valid_lb.pop(0), "l")
            else:
                nxt = (valid_rb.pop(0), "r")
        elif valid_lb:
            nxt = (valid_lb.pop(0), "l")
        else:
            nxt = (valid_rb.pop(0), "r")
        columns.append((position, nxt[0], nxt[1]))
        position = nxt[0]
    columns.append((columns[-1][1], None, "l"))

    # split right columns where there's something on the left in all rows
    # because that's actually a left column followed by a right column
    ncolumns = []
    for cs, ce, cj in columns:
        if cj == "r":
            try:
                start_characters = [
                    line[cs] != divider
                    for line in lines
                    if line.strip()
                ]
            except IndexError:
                start_characters = [False]
            if all(start_characters):
                # this right column has characters at the left in every row,
                # so it's probably two columns. Find a place to split it
                found = False
                for ncs in range(cs, ce):
                    is_spaces = [
                        line[ncs] == divider
                        for line in lines
                        if line.strip()
                    ]
                    if all(is_spaces):
                        ncolumns.append((cs, ncs, "l"))
                        ncolumns.append((ncs, ce, "r"))
                        found = True
                        break
                if not found:
                    # no place to split
                    ncolumns.append((cs, ce, cj))
            else:
                ncolumns.append((cs, ce, cj))
        else:
            ncolumns.append((cs, ce, cj))
    columns = ncolumns

    headers = []
    for start, end, justification in columns:
        headers.append(lines[0][start:end].strip())
    data = []

    # handle duplicate header keys
    newkeys = []
    bumpable = set()
    for i in range(len(headers)):
        this = headers[i]
        incr = 1
        while True:
            if [this, incr] in newkeys:
                incr += 1
                if this:
                    bumpable.add(this)
            else:
                newkeys.append([this, incr])
                break
    newheaders = [
        h if i == 1
        else "{}_{}".format(h, i)
        for (h, i) in newkeys
    ]
    for bump in list(bumpable):
        idx = newheaders.index(bump)
        newheaders[idx] = "{}_1".format(newheaders[idx])

    for line in lines[1:]:
        linedata = []
        for start, end, justification in columns:
            column = line[start:end].strip()
            linedata.append(column)

        valid_linedata = [
            x
            for x in zip(newheaders, linedata)
            if x[0] and x[1] and not x[0].startswith(divider)
        ]
        if valid_linedata:
            d = OrderedDict(valid_linedata)
            if "|" in d:
                del d["|"]
            data.append(d)
    return data


def output_ini(data: "Iterable[Dict]") -> None:
    for row in data:
        for k, v in row.items():
            print("{}={}".format(k, v))
        print()


def output_json(data: "Iterable[Dict]") -> None:
    print(json.dumps(list(data), indent=2))


def output_json_array_lines(data: "Iterable[Dict]") -> None:
    for row in data:
        print(json.dumps(list(row.values())))


def output_json_object_lines(data: "Iterable[Dict]") -> None:
    for row in data:
        print(json.dumps(row))


def output_csv(data: "Iterable[Dict]") -> None:
    import csv
    if not data:
        return
    fieldNames = OrderedDict([
        (key, None)
        for key in data[0].keys()
    ])
    writer = csv.DictWriter(
        sys.stdout,
        fieldnames=fieldNames,
    )
    writer.writeheader()
    for row in data:
        writer.writerow(row)


def output(data: "Iterable[Dict]", dformat: str) -> None:
    if dformat == "ini":
        output_ini(data)
    elif dformat == "json":
        output_json(data)
    elif dformat == "jsonal":
        output_json_array_lines(data)
    elif dformat == "jsonol":
        output_json_object_lines(data)
    elif dformat == "csv":
        output_csv(data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parse ASCII tabular data, such as command output",
    )
    parser.add_argument(
        "filename",
        default="-",
        nargs="?",
        help="file to parse or - (default) for stdin"
    )
    parser.add_argument(
        "--skip",
        type=int,
        default=0,
        help="lines to skip before table header",
    )
    parser.add_argument(
        "--format",
        default="csv",
        choices=[
            "ini",
            "json",
            "jsonal",
            "jsonol",
            "csv",
        ],
        help="output data format",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="show unfriendly tracebacks, not friendly errors",
    )
    args = parser.parse_args()
    try:
        data = parse(args.filename, args.skip)
        output(data, args.format)
    except IndexError:
        if args.debug:
            raise
        print(
            "That data does not seem to be tabular, so I am giving up.",
            file=sys.stderr,
        )
